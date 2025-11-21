from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import mediapipe as mp
import warnings
import base64
import collections
import time


warnings.filterwarnings("ignore")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

counter = 0
stage = None

angle_history = collections.deque(maxlen=60)  # store last 60 angles (2 seconds)
ptime = 0


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle

# Homepage
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Receive frames from browser camera
@app.post("/process_frame")
async def process_frame(file: UploadFile = File(...)):
    global counter, stage, angle_history, ptime

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    ctime = time.time()
    fps = 1 / (ctime - ptime) if ptime != 0 else 0
    ptime = ctime

    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        if result.pose_landmarks:

            landmarks = result.pose_landmarks.landmark
            
            shoulder = [
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            ]
            elbow = [
                landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y
            ]
            wrist = [
                landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
            ]

            angle = calculate_angle(shoulder, elbow, wrist)
            angle_history.append(angle)

            # position for angle display
            elbow_point = tuple(np.multiply(elbow, [frame.shape[1], frame.shape[0]]).astype(int))

            cv2.putText(frame, str(round(angle, 1)), elbow_point,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # REP LOGIC
            if angle > 160:
                stage = "Down"
            if angle < 45 and stage == "Down":
                stage = "Up"
                counter += 1

            # DRAW SKELETON
            mp_drawing.draw_landmarks(
                frame,
                result.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=4, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=3, circle_radius=2),
            )

    # REP COUNTER BOX
    cv2.rectangle(frame, (0, 0), (250, 120), (245, 117, 16), -1)
    cv2.putText(frame, "REPS", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(frame, str(counter), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 4)

    cv2.putText(frame, "STAGE", (130, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(frame, str(stage), (130, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)

    # FPS
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

    # ===============================
    # DRAW REAL-TIME ANGLE GRAPH
    # ===============================
    graph_h = 150
    graph_frame = np.zeros((graph_h, frame.shape[1], 3), dtype=np.uint8)

    if len(angle_history) > 1:
        for i in range(1, len(angle_history)):
            cv2.line(
                graph_frame,
                ( (i-1)*10, graph_h - int(angle_history[i-1]) ),
                ( i*10, graph_h - int(angle_history[i]) ),
                (0,255,0), 2
            )

    frame = np.vstack([frame, graph_frame])

    # Convert to JPEG Base64
    _, jpeg = cv2.imencode(".jpg", frame)
    jpg_base64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

    return {
        "frame": jpg_base64,
        "counter": counter,
        "stage": stage
    }
