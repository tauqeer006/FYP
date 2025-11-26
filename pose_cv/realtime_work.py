import cv2
import mediapipe as mp
import numpy as np
import yaml
import pyttsx3
import time
import threading

# ------------------ Pose Detector ------------------
class poseDetector():
    def __init__(self, mode=False, upBody=False, smooth=True, detectionCon=0.5, trackCon=0.5):
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(
            static_image_mode=mode,
            model_complexity=1,
            smooth_landmarks=smooth,
            enable_segmentation=False,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )

    def findPose(self, img, draw=False):     # draw=False removes lines
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        return img

    def findPosition(self, img):
        lmList = []
        if self.results.pose_landmarks:
            h, w, c = img.shape
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                lmList.append([id, int(lm.x*w), int(lm.y*h)])
        return lmList

    def findAngle(self, p1, p2, p3):
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


# ------------------ Load YAML ------------------
with open("new_exercise.yml") as f:
    exercises = yaml.safe_load(f)

exercise_names = [ex["name"] for ex in exercises["shoulder_rehab_exercises"]]
print("Available exercises:")
for i, name in enumerate(exercise_names):
    print(f"{i+1}. {name}")

choice = input("Enter the name of the exercise you want to perform: ").strip()
selected_exercise = next((ex for ex in exercises["shoulder_rehab_exercises"]
                          if ex["name"].strip().lower() == choice.lower()), None)
if not selected_exercise:
    print("Exercise not found!")
    exit()

print(f"Selected exercise: {selected_exercise['name']}")
print(f"Description: {selected_exercise['description']}")

# ------------------ Setup Webcam & TTS ------------------
cap = cv2.VideoCapture(0)
detector = poseDetector()
engine = pyttsx3.init()
tolerance = 7
cooldown = 2  # seconds between voice messages

def speak(text):
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run).start()

print("Starting in 3 seconds...")
time.sleep(3)
speak("Start performing the exercise. I will guide you.")

last_state = None
last_spoken_time = 0
correct_start_time = None

while True:
    success, img = cap.read()
    if not success:
        break

    img = detector.findPose(img, draw=False)  # NO LINES OR ANGLES
    lmList = detector.findPosition(img)

    posture_correct = True
    feedback_msgs = []

    if lmList:
        lmDict = {pt[0]: pt for pt in lmList}

        # Left arm
        left = selected_exercise["left_arm"]
        left_tips = selected_exercise.get("feedback_tips", {}).get("left", [])
        if all(k in lmDict for k in [11, 13, 15]):
            angle = detector.findAngle(lmDict[11], lmDict[13], lmDict[15])
            if abs(angle - left["shoulder_angle"]) > tolerance:
                posture_correct = False
                feedback_msgs.extend(left_tips)

        # Right arm
        right = selected_exercise["right_arm"]
        right_tips = selected_exercise.get("feedback_tips", {}).get("right", [])
        if all(k in lmDict for k in [12, 14, 16]):
            angle = detector.findAngle(lmDict[12], lmDict[14], lmDict[16])
            if abs(angle - right["shoulder_angle"]) > tolerance:
                posture_correct = False
                feedback_msgs.extend(right_tips)

    now = time.time()

    # ------------------ Voice feedback ------------------
    if posture_correct:
        if correct_start_time is None:
            correct_start_time = now
        if now - correct_start_time >= 5 and (last_state != "improving" or now - last_spoken_time > cooldown):
            speak("You are improving! Try again.")
            last_state = "improving"
            last_spoken_time = now
    else:
        correct_start_time = None
        if feedback_msgs and (last_state != "incorrect" or now - last_spoken_time > cooldown):
            speak(" ".join(feedback_msgs))
            last_state = "incorrect"
            last_spoken_time = now

    # ------------------ Simple Visual Feedback ------------------
    y_offset = 30
    for msg in feedback_msgs:
        cv2.putText(img, msg, (10, y_offset), cv2.FONT_HERSHEY_PLAIN, 1.6, (0, 0, 255), 2)
        y_offset += 30

    if posture_correct:
        cv2.putText(img, "Posture Correct!", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    cv2.imshow("Shoulder Exercise Feedback", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
