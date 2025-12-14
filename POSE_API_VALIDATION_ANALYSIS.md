# Pose API Exercise Name Validation Analysis

## Overview
The Pose API is a FastAPI service running on port 5003 that validates user posture during shoulder rehabilitation exercises. The API is located in `pose_cv/app.py` and uses a YAML configuration file (`pose_cv/new_exercise.yml`) to define valid exercises.

---

## 1. Exercise Name Validation Function

### `find_exercise()` Function
**Location:** [pose_cv/app.py](pose_cv/app.py#L218)

```python
def find_exercise(exercise_name: str):
    """Find exercise by name"""
    for ex in exercises:
        if ex["name"].strip().lower() == exercise_name.strip().lower():
            return ex
    return None
```

**Behavior:**
- **Input:** Exercise name as a string
- **Search:** Case-insensitive comparison against loaded exercises
- **Return on match:** Returns the full exercise dictionary (contains name, description, left_arm, right_arm, feedback_tips, video)
- **Return on no match:** Returns `None`
- **Validation:** String comparison is case-insensitive and strips whitespace

**Usage in API:**
- Called in `/api/check-pose` endpoint (line 480) to validate exercise before processing
- Called in `/api/validate-exercise` endpoint (line 509) to check if exercise exists
- Called in `/api/exercises` endpoint (line 527) for exercise listing

---

## 2. Valid Exercise Names

**Source:** [pose_cv/new_exercise.yml](pose_cv/new_exercise.yml)

The following exercises are currently valid and expected by the backend:

1. **Pendulum Swing**
   - Left arm: 45°, Right arm: 45°
   - Description: Lean forward and let the injured arm hang, then gently swing it in small circles

2. **Active Shoulder Flexion (Wall Slide)**
   - Left arm: 90°, Right arm: 90°
   - Description: Face a wall, slide the arm up the wall slowly to shoulder height or above

3. **Shoulder Abduction (Assisted)**
   - Left arm: 90°, Right arm: 90°
   - Description: Using a cane or stick, assist the arm out to the side to shoulder height

4. **External Rotation with Band (Elbow at Side)**
   - Left arm: 20°, Right arm: 20°
   - Description: With elbow tucked and forearm rotating outwards using a light band

5. **Internal Rotation with Band (Elbow at Side)**
   - Left arm: 20°, Right arm: 20°
   - Description: With elbow tucked and forearm rotating inward using a band

6. **Scapular Retraction/Depression (Wall Slide Variation)**
   - Left arm: 90°, Right arm: 90°
   - Description: While sliding arms up the wall, focus on pulling shoulder blades down and back

7. **Prone Y Raise (on bed or table)**
   - Left arm: 135°, Right arm: 135°
   - Description: Lying face down on a table with arms raised into a "Y" shape

8. **Wall Angel (with scapular control)**
   - Left arm: 135°, Right arm: 135°
   - Description: Standing back against wall, slide arms up and down in "snow-angel" motion

9. **Seated Shoulder Flexion (Using Assistive Device)**
   - Left arm: 90°, Right arm: 90°
   - Description: Sitting upright, raise arm(s) forward with assistance or support

10. **Side-lying External Rotation (Low Load)**
    - Left arm: 30°, Right arm: 30°
    - Description: Lie on side, elbow bent 90°, keep upper arm supported and rotate forearm

11. **Isometric Shoulder Flexion**
    - Left arm: 90°, Right arm: 90°
    - Description: Stand near wall, press fist or forearm into wall at shoulder level

12. **Scaption (Scapular-Plane Elevation)**
    - Left arm: 90°, Right arm: 90°
    - Description: Raise arms in front at about 30° from the body (in scapular plane)

13. **External Rotation in 90° Abduction**
    - Left arm: 90°, Right arm: 90°
    - Description: In 90° shoulder abduction position, rotate forearm upward/outward

14. **Shoulder Horizontal Abduction (Prone)**
    - Left arm: 90°, Right arm: 90°
    - Description: Lie face down on table with arms out front, then move arms horizontally

15. **Shoulder Extension (Standing Assisted)**
    - Left arm: 40°, Right arm: 40°
    - Description: In standing, use a stick or assistive device to move arm backward

16. **Chair Push-Up for Shoulder (Mini)**
    - Left arm: 60°, Right arm: 60°
    - Description: Place hands on chair or table, do mini push-ups that activate scapular stability

17. **I-Y-T Raise (Scapular Activation)**
    - Left arm: 135°, Right arm: 135°
    - Description: Lie prone or stand bent forward and move arms in I, Y, and T shapes

18. **Serratus Punch**
    - Left arm: 120°, Right arm: 120°
    - Description: Standing or lying, punch forward upward at about 120° to activate serratus anterior

19. **Shoulder Flexion in Side-lying (Low Load)**
    - Left arm: 90°, Right arm: 0° (asymmetric - right side unaffected)
    - Description: Lie on side with unaffected arm down, lift affected arm in front

20. **Arm Across Chest Stretch (Post-Mobility)**
    - Left arm: 45°, Right arm: 45°
    - Description: Bring one arm across the chest and use other to support it

21. **Assisted Overhead Reach (Seated or Supported)**
    - Left arm: 150°, Right arm: 150°
    - Description: Seated with back support, use stick or cane to gently assist overhead reach

22. **Gentle Shoulder Abduction from Side-lying**
    - Left arm: 80°, Right arm: 0° (asymmetric)
    - Description: Lie on opposite side and lift arm out to side to about 70-90°

23. **Wall Walks – Finger Walks Up Wall**
    - Left arm: 110°, Right arm: 110°
    - Description: Face wall and "walk" fingers up the wall as high as comfortable

---

## 3. `check_posture()` Function Implementation

**Location:** [pose_cv/app.py](pose_cv/app.py#L226)

```python
def check_posture(img, exercise, session_id="default"):
    """Check if user's posture matches exercise requirements with lenient 50% correctness"""
```

### Function Signature
- **Parameters:**
  - `img`: OpenCV image to process
  - `exercise`: Exercise dictionary returned by `find_exercise()`
  - `session_id`: String identifier for tracking reps across frames (default: "default")

- **Return Values (8 values):**
  1. `is_correct` (bool): Whether posture is correct
  2. `message` (str): User-facing message (e.g., "✅ Perfect! Keep it up!")
  3. `feedback` (str): Detailed angle feedback
  4. `angles_detected` (dict): Detected angles like `{"left_shoulder": 45, "right_shoulder": 50}`
  5. `angle_details` (list): Detailed breakdown per arm with current/target angles and status
  6. `rep_count` (int): Current rep count for this session
  7. `frames_in_rep` (int): Frames completed in current rep (0-30)
  8. `shoulder_positions` (dict): Shoulder landmark coordinates for UI overlay

### Core Logic

1. **Invalid Image Check:**
   ```python
   if img is None or img.size == 0:
       return False, "❌ Could not process image", "", {}, [], 0, {}, {}
   ```

2. **Pose Detection:**
   - Uses MediaPipe to detect 33 body landmarks
   - Extracts shoulder and elbow/wrist positions
   - Calculates shoulder angles for both left (landmarks 11-13-15) and right (landmarks 12-14-16) arms

3. **Angle Calculation:**
   - Uses `detector.findAngle()` to calculate angles between three points (shoulder-elbow-wrist)
   - Compares detected angle to target angle from exercise definition
   - Tolerance: **1 degree** (TOLERANCE = 1)

4. **Validation Criteria:**
   - **EXTREMELY LENIENT:** Accepts frame as correct if:
     - At least 1 arm is within tolerance, **OR**
     - Correctness percentage is ≥ 10% (at least 10% threshold met)
   
   ```python
   correctness_percentage = (correct_count / total_arms) * 100
   posture_correct = (correct_count > 0) or (correctness_percentage >= 10)
   ```

5. **Rep Counting:**
   - Tracks consecutive correct frames per session
   - **30 consecutive correct frames = 1 rep**
   - Resets counter on incorrect frame
   - Session storage: `exercise_sessions = {session_id: {"consecutive_correct": int, "total_reps": int}}`

6. **Feedback Generation:**
   - If correct: `✅ Perfect! Keep it up! (Frame X/30 for rep Y)`
   - If incorrect: `📍 Not quite there yet - adjust and try again!`
   - Per-arm feedback: `Left: 45° (target 90°) - 📈 Raise arm UP`

### Landmark Indices (MediaPipe)
- **11:** Left Shoulder
- **12:** Right Shoulder
- **13:** Left Elbow
- **14:** Right Elbow
- **15:** Left Wrist
- **16:** Right Wrist

---

## 4. Error Handling for Invalid/Missing Exercise Names

### `/api/check-pose` Endpoint
**Location:** [pose_cv/app.py](pose_cv/app.py#L476)

```python
@app.post("/api/check-pose")
async def check_pose(request: PoseCheckRequest):
    """Check if user's posture matches exercise requirements"""
    # Validate exercise exists
    exercise = find_exercise(request.exercise_name)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{request.exercise_name}' not found")
```

**Error Response:**
- **Status Code:** 404 Not Found
- **Response Body:** 
  ```json
  {
    "detail": "Exercise 'InvalidExerciseName' not found"
  }
  ```

### `/api/validate-exercise` Endpoint
**Location:** [pose_cv/app.py](pose_cv/app.py#L501)

```python
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
```

**Error Response (if not found):**
- **Status Code:** 200 OK (still returns 200)
- **Response Body:**
  ```json
  {
    "valid": false,
    "message": "Exercise 'InvalidExerciseName' not found"
  }
  ```

---

## 5. Pydantic Request Models

### PoseCheckRequest
**Location:** [pose_cv/app.py](pose_cv/app.py#L115)

```python
class PoseCheckRequest(BaseModel):
    exercise_name: str
    image: str  # base64 encoded image
    session_id: str = "default"
```

### ExerciseInfo
```python
class ExerciseInfo(BaseModel):
    name: str  # Exercise name to validate
```

---

## 6. Key Configuration Details

### Exercise YAML Structure
Each exercise in `new_exercise.yml` contains:
```yaml
- name: "Exercise Name"
  description: "Description"
  left_arm:
    shoulder_angle: 90
    elbow_angle: 180
  right_arm:
    shoulder_angle: 90
    elbow_angle: 180
  feedback_tips:
    left:
      - "Left arm tip 1"
      - "Left arm tip 2"
    right:
      - "Right arm tip 1"
      - "Right arm tip 2"
  video: "https://..."
```

### Session Tracking
- Sessions are tracked in memory in `exercise_sessions` dictionary
- Each session maintains:
  - `consecutive_correct`: Counter for frames in current rep
  - `total_reps`: Total completed reps
- Sessions persist during API runtime but are lost on restart

---

## 7. Summary of Validation Flow

```
User sends request with exercise_name
    ↓
find_exercise(exercise_name) called
    ↓
Search exercises list (case-insensitive)
    ├─ MATCH FOUND → Return exercise dict
    └─ NO MATCH → Return None
    ↓
If None:
    └─ /api/check-pose: HTTPException 404
    └─ /api/validate-exercise: Return {valid: false, message: "...not found"}
    ↓
If exercise found:
    └─ check_posture(img, exercise, session_id)
        └─ Detect pose landmarks
        └─ Calculate angles for both arms
        └─ Compare to exercise targets
        └─ Track rep count
        └─ Return 8-tuple with results
```

---

## Important Notes

1. **Case Insensitivity:** Exercise names are matched case-insensitively (e.g., "pendulum swing" == "PENDULUM SWING")
2. **Lenient Validation:** The API is very permissive - only needs 1 arm correct or 10% threshold
3. **Real-Time Rep Counting:** 30 consecutive frames = 1 rep (approximately 1 second at 30fps)
4. **MediaPipe Dependency:** Requires MediaPipe pose detection to work
5. **No Database:** Exercise list is loaded from YAML file at startup
6. **Session Isolation:** Each session_id maintains independent rep counts
