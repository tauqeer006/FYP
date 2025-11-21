
GYM Pose Estimation using MediaPipe

This project implements real-time pose estimation using MediaPipe to track body movements during gym exercises. It analyzes the angle between the shoulder, elbow, and wrist to count repetitions and provide visual feedback on exercise stages (e.g., Down, Up).

Features:

Real-time pose detection with MediaPipe's pose solution
Calculation of the elbow angle for rep counting during arm movements
Stage detection (Down/Up) based on the elbow angle threshold
Display of current rep count and exercise stage on the video frame
Visualization of detected body landmarks and connections
Requirements:

Python 3.x
OpenCV (pip install opencv-python)
MediaPipe (pip install mediapipe)
NumPy (pip install numpy)


Advanced Usage (Optional):

Left/Right Hand Detection:
The code can be extended to determine the relative position (Left, Right, Far) of body parts. Define thresholds for landmark X and Y coordinates to classify positions. Consider factors like frame width and camera angle for threshold adjustments.
Choose appropriate landmarks based on your use case (e.g., wrist for hand position, shoulder for upper body orientation).
Distance-Based Far Detection:
Implement a distance metric (like Euclidean distance) from a reference point (e.g., frame center) to a landmark. Classify a landmark as Far if the distance exceeds a threshold.
Explore combining position and distance for more robust Far detection.
