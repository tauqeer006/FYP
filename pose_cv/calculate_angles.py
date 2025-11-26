import cv2
import mediapipe as mp
import numpy as np
import yaml
import os

# -----------------------------
# Angle Calculation Function
# -----------------------------
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

    return angle

# -----------------------------
# Mediapipe Pose Model
# -----------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False)

# -----------------------------
# Process a Single Video
# -----------------------------
def process_video(video_path, output_yml):
    cap = cv2.VideoCapture(video_path)
    frame_index = 0

    data = {
        "video": os.path.basename(video_path),
        "frames": []
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            continue

        lm = results.pose_landmarks.landmark

        def p(id):
            return [lm[id].x, lm[id].y]

        # Body landmarks
        left_shoulder  = p(11)
        right_shoulder = p(12)
        left_elbow     = p(13)
        right_elbow    = p(14)
        left_wrist     = p(15)
        right_wrist    = p(16)
        left_hip       = p(23)
        right_hip      = p(24)
        left_knee      = p(25)
        right_knee     = p(26)
        left_ankle     = p(27)
        right_ankle    = p(28)

        # -----------------------------------------
        # Angle Calculations
        # -----------------------------------------
        shoulder_tilt = calculate_angle(right_shoulder, left_shoulder, left_hip)

        left_elbow_angle  = calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

        left_knee_angle   = calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle  = calculate_angle(right_hip, right_knee, right_ankle)

        back_angle = calculate_angle(left_shoulder, left_hip, left_knee)

        frame_data = {
            "frame_number": frame_index,
            "landmarks": {
                "left_shoulder": left_shoulder,
                "right_shoulder": right_shoulder,
                "left_elbow": left_elbow,
                "right_elbow": right_elbow,
                "left_wrist": left_wrist,
                "right_wrist": right_wrist,
                "left_hip": left_hip,
                "right_hip": right_hip,
                "left_knee": left_knee,
                "right_knee": right_knee,
                "left_ankle": left_ankle,
                "right_ankle": right_ankle
            },
            "angles": {
                "shoulder_tilt": float(shoulder_tilt),
                "left_elbow_angle": float(left_elbow_angle),
                "right_elbow_angle": float(right_elbow_angle),
                "left_knee_angle": float(left_knee_angle),
                "right_knee_angle": float(right_knee_angle),
                "back_angle": float(back_angle)
            }
        }

        data["frames"].append(frame_data)

    cap.release()

    # Save YAML
    with open(output_yml, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    print(f"Saved YAML: {output_yml}")

# -----------------------------------
# Main Loop — Process ALL FOLDERS
# -----------------------------------
video_folders = [
    "boneanomaly",
    "bonelesion",
    "foreignbody",
    "fracture",
    "metal",
    "periostealreaction",
    "pronatorsign",
    "Simple exercise",
    "softtissue"
]

output_base = "output"
os.makedirs(output_base, exist_ok=True)

for folder in video_folders:
    input_path = folder
    output_path = os.path.join(output_base, folder)

    os.makedirs(output_path, exist_ok=True)

    for file in os.listdir(input_path):
        if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):

            video_path = os.path.join(input_path, file)
            yaml_filename = file.rsplit(".", 1)[0] + ".yml"
            yaml_path = os.path.join(output_path, yaml_filename)

            print(f"Processing: {video_path}")
            process_video(video_path, yaml_path)

print("Done! All folders processed.")
