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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
detector = poseDetector()
exercises = load_exercises()
TOLERANCE = 7  # Tolerance for angle matching
tts_engine = pyttsx3.init()


# ==================== Pydantic Models ====================
class PoseCheckRequest(BaseModel):
    exercise_name: str
    image: str  


class ExerciseInfo(BaseModel):
    name: str
    description: str


class PoseCheckResponse(BaseModel):
    correct: bool
    message: str
    feedback: str = ""
    angles: dict = {}


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


def check_posture(img, exercise):
    """Check if user's posture matches exercise requirements"""
    if img is None or img.size == 0:
        return False, "Could not process image", "", {}

    detector.findPose(img, draw=False)
    lmList = detector.findPosition(img)

    posture_correct = True
    feedback_msgs = []
    angles_detected = {}

    if lmList:
        lmDict = {pt[0]: pt for pt in lmList}

        # Check Left Arm
        left = exercise.get("left_arm", {})
        left_tips = exercise.get("feedback_tips", {}).get("left", [])
        
        if left.get("shoulder_angle", 0) > 0 and all(k in lmDict for k in [11, 13, 15]):
            angle = detector.findAngle(lmDict[11], lmDict[13], lmDict[15])
            angles_detected["left_shoulder"] = angle
            target = left.get("shoulder_angle", 0)
            
            if abs(angle - target) > TOLERANCE:
                posture_correct = False
                feedback_msgs.extend(left_tips)

        # Check Right Arm
        right = exercise.get("right_arm", {})
        right_tips = exercise.get("feedback_tips", {}).get("right", [])
        
        if right.get("shoulder_angle", 0) > 0 and all(k in lmDict for k in [12, 14, 16]):
            angle = detector.findAngle(lmDict[12], lmDict[14], lmDict[16])
            angles_detected["right_shoulder"] = angle
            target = right.get("shoulder_angle", 0)
            
            if abs(angle - target) > TOLERANCE:
                posture_correct = False
                feedback_msgs.extend(right_tips)
    else:
        return False, "No pose detected", "Please adjust your position to be visible in the camera", {}

    feedback = " | ".join(feedback_msgs) if feedback_msgs else "Keep up the good work!"
    message = "Posture Correct! ✓" if posture_correct else "Adjust your position"

    return posture_correct, message, feedback, angles_detected


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
    
    # Check posture (fast)
    is_correct, message, feedback, angles = check_posture(img, exercise)
    
    response = PoseCheckResponse(
        correct=is_correct,
        message=message,
        feedback=feedback,
        angles=angles
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
