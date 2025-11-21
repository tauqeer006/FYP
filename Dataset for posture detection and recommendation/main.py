import cv2
import os

input_folder = "videos"
output_folder = "avi_dataset"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith((".mov", ".mp4", ".avi")):  # accept all formats
        input_path = os.path.join(input_folder, filename)
        output_filename = os.path.splitext(filename)[0] + ".avi"
        output_path = os.path.join(output_folder, output_filename)

        print(f"🔄 Processing: {input_path}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print(f"❌ Cannot open video: {input_path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 25  # fallback if fps=0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Use XVID codec (widely supported for AVI)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()

        print(f"✅ Saved {output_filename} ({frame_count} frames)")

print("🎯 AVI conversion completed.")
