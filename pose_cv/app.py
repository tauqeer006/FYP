from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import yaml
import base64
from io import BytesIO
import threading
import pyttsx3
import time
from pydantic import BaseModel
import uvicorn
import mediapipe as mp
import logging
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Pose Detector Class ====================
class poseDetector:
    def __init__(self, mode=False, smooth=True, detectionCon=0.5, trackCon=0.5):
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(
            static_image_mode=mode,
            model_complexity=1,
            smooth_landmarks=smooth,
            enable_segmentation=False,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.last_results = None

    def findPose(self, img, draw=False):
        """Process image and detect pose"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.last_results = self.pose.process(imgRGB)
        return img

    def findPosition(self, img):
        """Extract landmark positions"""
        lmList = []
        if self.last_results and self.last_results.pose_landmarks:
            h, w, c = img.shape
            for id, lm in enumerate(self.last_results.pose_landmarks.landmark):
                lmList.append([id, int(lm.x*w), int(lm.y*h)])
        return lmList

    def findAngle(self, p1, p2, p3):
        """Calculate angle between three points"""
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        x3, y3 = p3[1], p3[2]

        a = np.array([x1 - x2, y1 - y2])
        b = np.array([x3 - x2, y3 - y2])

        if np.linalg.norm(a) < 1e-6 or np.linalg.norm(b) < 1e-6:
            return 0

        cosine_angle = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return int(angle)


# ==================== Load Exercises from YAML ====================
def load_exercises():
    """Load exercises from YAML file"""
    try:
        with open("new_exercise.yml", "r") as f:
            data = yaml.safe_load(f)
        return data.get("shoulder_rehab_exercises", [])
    except FileNotFoundError:
        logger.error("Exercise YAML file not found")
        return []


# ==================== FastAPI App ====================
app = FastAPI(title="Shoulder Rehabilitation API", version="1.0.0")

# Add CORS middleware with configurable origins
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)

# Global variables
detector = poseDetector()
exercises = load_exercises()
TOLERANCE = 50  # EXTREMELY LENIENT: ±50° tolerance - barely any effort counts as correct
tts_engine = pyttsx3.init()

# Session tracking for rep counting
exercise_sessions = {}  # {session_id: {"consecutive_correct": int, "total_reps": int}}


# ==================== Health Check ====================
@app.get('/api/health')
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        'status': 'ok',
        'service': 'pose-api',
        'version': '1.0.0'
    }


# ==================== Pydantic Models ====================
class PoseCheckRequest(BaseModel):
    exercise_name: str
    image: str
    session_id: str = "default"  # Session ID for tracking reps across frames


class ExerciseInfo(BaseModel):
    name: str
    description: str


class PoseCheckResponse(BaseModel):
    correct: bool
    message: str
    feedback: str = ""
    angles: dict = {}
    angle_details: list = []  # New: Specific angle feedback
    rep_count: int = 0  # New: Number of completed reps
    frames_in_rep: int = 0  # New: Current frame count towards next rep (0-30)


class ExerciseSession(BaseModel):
    """Track exercise session state"""
    exercise_name: str
    consecutive_correct: int = 0  # Track consecutive correct frames
    total_reps: int = 0  # Total completed reps
    frames_per_rep: int = 30  # Frames needed to complete one rep (adjustable)


# ==================== Helper Functions ====================
def speak_async(text):
    """Speak text in a separate thread"""
    def run():
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def generate_audio_base64(text):
    """Generate audio from text and return as base64 encoded string (optimized)"""
    try:
        # Skip audio generation for very short texts
        if not text or len(text) < 5:
            return ""
        
        # Create a temporary file to store audio
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Use existing global TTS engine or create new one
            audio_engine = pyttsx3.init()
            audio_engine.setProperty('rate', 150)  # Speed
            
            # Save to file with minimal overhead
            audio_engine.save_to_file(text, tmp_path)
            audio_engine.runAndWait()
            
            # Read and encode quickly
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    logger.info(f"✓ Audio generated: {len(audio_base64)} bytes")
                    return audio_base64
        finally:
            # Always clean up
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
        
        return ""
    except Exception as e:
        logger.warning(f"Audio skipped: {str(e)[:50]}")
        return ""


def base64_to_image(image_data: str):
    """Convert base64 string to OpenCV image"""
    try:
        # Remove data URI scheme if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None


def find_exercise(exercise_name: str):
    """Find exercise by name"""
    for ex in exercises:
        if ex["name"].strip().lower() == exercise_name.strip().lower():
            return ex
    return None


def check_posture(img, exercise, session_id="default"):
    """Check if user's posture matches exercise requirements with lenient 50% correctness"""
    if img is None or img.size == 0:
        logger.warning("❌ Invalid image received")
        return False, "❌ Could not process image", "", {}, [], 0

    detector.findPose(img, draw=False)
    lmList = detector.findPosition(img)
    
    logger.info(f"🔍 Detected {len(lmList)} landmarks for exercise: {exercise.get('name', 'Unknown')}")

    feedback_msgs = []
    angles_detected = {}
    specific_feedback = []  # New: More specific feedback
    correct_count = 0  # Count how many arms are correct
    total_arms = 0  # Total arms being checked

    if lmList and len(lmList) > 0:
        lmDict = {pt[0]: pt for pt in lmList}
        left_correct = False
        right_correct = False

        # ALWAYS Calculate LEFT Arm angle - regardless of target value
        left = exercise.get("left_arm", {})
        left_tips = exercise.get("feedback_tips", {}).get("left", [])
        
        # Try to detect left arm - always attempt to get the angle
        if all(k in lmDict for k in [11, 13, 15]):
            total_arms += 1
            angle = detector.findAngle(lmDict[11], lmDict[13], lmDict[15])
            angles_detected["left_shoulder"] = angle
            target = left.get("shoulder_angle", 0) if left.get("shoulder_angle", 0) > 0 else 90  # Default target if not set
            difference = abs(angle - target)
            
            logger.info(f"👈 Left Arm: Current {angle}° vs Target {target}° (diff: {difference}°, tolerance: {TOLERANCE}°)")
            
            specific_feedback.append({
                "arm": "Left",
                "current_angle": int(angle),
                "target_angle": int(target),
                "difference": int(difference)
            })
            
            if difference <= TOLERANCE:
                left_correct = True
                correct_count += 1
                specific_feedback[-1]["status"] = "✅ Correct"
                logger.info(f"✅ LEFT ARM CORRECT!")
            else:
                if left_tips:
                    feedback_msgs.extend(left_tips)
                # More specific guidance
                if angle < target:
                    specific_feedback[-1]["status"] = "📈 Raise arm UP"
                else:
                    specific_feedback[-1]["status"] = "📉 Lower arm DOWN"
        else:
            logger.warning(f"⚠️ Left arm landmarks not found. Available: {list(lmDict.keys())}")
            angles_detected["left_shoulder"] = 0  # Send 0 to indicate not visible

        # ALWAYS Calculate RIGHT Arm angle - regardless of target value
        right = exercise.get("right_arm", {})
        right_tips = exercise.get("feedback_tips", {}).get("right", [])
        
        # Try to detect right arm even if no specific target is set
        if all(k in lmDict for k in [12, 14, 16]):
            total_arms += 1
            angle = detector.findAngle(lmDict[12], lmDict[14], lmDict[16])
            angles_detected["right_shoulder"] = angle
            target = right.get("shoulder_angle", 0) if right.get("shoulder_angle", 0) > 0 else 90  # Default target
            difference = abs(angle - target)
            
            logger.info(f"👉 Right Arm: Current {angle}° vs Target {target}° (diff: {difference}°, tolerance: {TOLERANCE}°)")
            
            specific_feedback.append({
                "arm": "Right",
                "current_angle": int(angle),
                "target_angle": int(target),
                "difference": int(difference)
            })
            
            if difference <= TOLERANCE:
                right_correct = True
                correct_count += 1
                specific_feedback[-1]["status"] = "✅ Correct"
                logger.info(f"✅ RIGHT ARM CORRECT!")
            else:
                if right_tips:
                    feedback_msgs.extend(right_tips)
                # More specific guidance
                if angle < target:
                    specific_feedback[-1]["status"] = "📈 Raise arm UP"
                else:
                    specific_feedback[-1]["status"] = "📉 Lower arm DOWN"
        else:
            # If right shoulder landmarks not found, still send 0 so frontend knows we tried
            logger.warning(f"⚠️ Right arm landmarks not found. Available landmarks: {list(lmDict.keys())}")
            angles_detected["right_shoulder"] = 0  # Send 0 to indicate not visible
            
            specific_feedback.append({
                "arm": "Right",
                "current_angle": 0,
                "target_angle": right.get("shoulder_angle", 90),
                "difference": 999,
                "status": "⚠️ Adjust position - arm not visible"
            })
    else:
        logger.warning(f"❌ No pose detected! Landmarks found: {len(lmList) if lmList else 0}")
        return False, "❌ No pose detected", "📸 Please move into camera view and stand clearly", {}, [], 0, 0

    logger.info(f"📊 Results: Total arms checked: {total_arms}, Correct count: {correct_count}")

    # EXTREMELY LENIENT: Accept if even 1 arm is close OR 10% threshold
    posture_correct = False
    if total_arms > 0:
        correctness_percentage = (correct_count / total_arms) * 100
        # If at least 1 arm is correct OR 10% threshold is met, mark as correct
        posture_correct = (correct_count > 0) or (correctness_percentage >= 10)
        logger.info(f"✔️ Frame Analysis:")
        logger.info(f"   - Total arms checked: {total_arms}")
        logger.info(f"   - Correct arms: {correct_count}")
        logger.info(f"   - Correctness %: {correctness_percentage:.1f}%")
        logger.info(f"   - Decision: {'✅ CORRECT - Frame Counts!' if posture_correct else '❌ INCORRECT - Reset counter'}")
    
    # Track rep count in session
    if session_id not in exercise_sessions:
        exercise_sessions[session_id] = {"consecutive_correct": 0, "total_reps": 0}
        logger.info(f"📝 NEW SESSION CREATED: {session_id}")
    
    session = exercise_sessions[session_id]
    rep_count = session["total_reps"]
    
    if posture_correct:
        session["consecutive_correct"] += 1
        logger.info(f"✅ CORRECT FRAME! Session {session_id[-8:]}: {session['consecutive_correct']}/30 frames")
        # Every 30 consecutive correct frames = 1 rep
        if session["consecutive_correct"] >= 30:
            session["total_reps"] += 1
            session["consecutive_correct"] = 0  # Reset counter for next rep
            rep_count = session["total_reps"]
            logger.info(f"🎉 REP #{rep_count} COMPLETED!")
    else:
        # Reset consecutive counter on incorrect frame
        if session["consecutive_correct"] > 0:
            logger.info(f"❌ WRONG FRAME! Reset counter from {session['consecutive_correct']} to 0. Session: {session_id[-8:]}")
        session["consecutive_correct"] = 0
    
    # Enhanced feedback messages
    if posture_correct:
        feedback_parts = []
        for sf in specific_feedback:
            feedback_parts.append(
                f"{sf['arm']}: {sf['current_angle']}° (target {sf['target_angle']}°) - {sf.get('status', '')}"
            )
        feedback = " | ".join(feedback_parts) if feedback_parts else "Good effort!"
        
        # Show progress towards next rep
        frames_in_rep = session["consecutive_correct"]
        if frames_in_rep == 30:
            message = f"🎉 Rep {rep_count} Complete! Starting rep {rep_count + 1}..."
        else:
            message = f"✅ Perfect! Keep it up! (Frame {frames_in_rep}/30 for rep {rep_count + 1})"
    else:
        feedback_parts = []
        for sf in specific_feedback:
            feedback_parts.append(
                f"{sf['arm']}: {sf['current_angle']}° (need {sf['target_angle']}°) - {sf.get('status', '')}"
            )
        feedback = " | ".join(feedback_parts) if feedback_parts else "Keep practicing!"
        frames_in_rep = 0
        message = "📍 Not quite there yet - adjust and try again!"

    # DEBUG: Log what we're returning
    logger.info(f"📤 RETURNING ANGLES TO FRONTEND: {angles_detected}")
    logger.info(f"   - Left Shoulder: {angles_detected.get('left_shoulder', 'NOT SENT')}")
    logger.info(f"   - Right Shoulder: {angles_detected.get('right_shoulder', 'NOT SENT')}")
    
    return posture_correct, message, feedback, angles_detected, specific_feedback, rep_count, frames_in_rep


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "Shoulder Rehabilitation API is running",
        "version": "1.0.0",
        "endpoints": {
            "exercises": "/api/exercises",
            "check_pose": "/api/check-pose",
            "exercise_info": "/api/exercise/{exercise_name}"
        }
    }


@app.get("/api/exercises")
async def get_exercises():
    """Get all available exercises"""
    exercise_list = [
        {
            "name": ex["name"],
            "description": ex["description"],
            "video": ex.get("video", "")
        }
        for ex in exercises
    ]
    return {
        "total": len(exercise_list),
        "exercises": exercise_list
    }


@app.get("/api/exercise/{exercise_name}")
async def get_exercise_info(exercise_name: str):
    """Get detailed information about a specific exercise"""
    exercise = find_exercise(exercise_name)
    
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{exercise_name}' not found")
    
    return {
        "name": exercise.get("name"),
        "description": exercise.get("description"),
        "left_arm": exercise.get("left_arm", {}),
        "right_arm": exercise.get("right_arm", {}),
        "feedback_tips": exercise.get("feedback_tips", {}),
        "video": exercise.get("video", "")
    }


@app.post("/api/check-pose")
async def check_pose(request: PoseCheckRequest):
    """Check if user's posture matches exercise requirements"""
    # Validate exercise exists
    exercise = find_exercise(request.exercise_name)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{request.exercise_name}' not found")
    
    # Convert base64 image to OpenCV format
    img = base64_to_image(request.image)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image data")
    
    # Check posture (fast) - now returns 7 values including frames_in_rep
    is_correct, message, feedback, angles, angle_details, rep_count, frames_in_rep = check_posture(img, exercise, request.session_id)
    
    response = PoseCheckResponse(
        correct=is_correct,
        message=message,
        feedback=feedback,
        angles=angles,
        angle_details=angle_details,
        rep_count=rep_count,
        frames_in_rep=frames_in_rep
    )
    
    return response


@app.post("/api/validate-exercise")
async def validate_exercise(request: ExerciseInfo):
    """Validate if an exercise exists in the database"""
    exercise = find_exercise(request.name)
    
    if exercise:
        return {
            "valid": True,
            "exercise_name": exercise.get("name"),
            "description": exercise.get("description")
        }
    else:
        return {
            "valid": False,
            "message": f"Exercise '{request.name}' not found"
        }


@app.post("/api/start-exercise")
async def start_exercise(request: ExerciseInfo):
    """Start an exercise session"""
    exercise = find_exercise(request.name)
    
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{request.name}' not found")
    
    # Speak instructions
    speak_async(f"Starting exercise: {exercise.get('name')}. {exercise.get('description')}")
    
    return {
        "status": "exercise_started",
        "exercise_name": exercise.get("name"),
        "instructions": exercise.get("description"),
        "feedback_tips": exercise.get("feedback_tips", {})
    }


@app.post("/api/reset-session/{session_id}")
async def reset_session(session_id: str):
    """Reset/clear exercise session for rep counting"""
    if session_id in exercise_sessions:
        exercise_sessions[session_id] = {"consecutive_correct": 0, "total_reps": 0}
    
    return {
        "status": "session_reset",
        "session_id": session_id,
        "reps": 0,
        "consecutive_correct": 0
    }


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information including rep count"""
    if session_id not in exercise_sessions:
        return {
            "session_id": session_id,
            "total_reps": 0,
            "consecutive_correct": 0,
            "status": "no_session"
        }
    
    session = exercise_sessions[session_id]
    return {
        "session_id": session_id,
        "total_reps": session["total_reps"],
        "consecutive_correct": session["consecutive_correct"],
        "status": "active"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "exercises_loaded": len(exercises) > 0,
        "total_exercises": len(exercises)
    }


# ==================== Run Server ====================
if __name__ == "__main__":
    logger.info(f"Loaded {len(exercises)} exercises from YAML")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
