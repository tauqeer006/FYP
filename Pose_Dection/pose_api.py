from flask import Flask, request, jsonify
import cv2
import numpy as np
from collections import deque
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import mediapipe as mp
import base64
import io
from PIL import Image

app = Flask(__name__)

# Load trained LSTM autoencoder
model = load_model("exercise_autoencoder.h5", compile=False)

# Mediapipe Pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)

# Thresholds
THRESHOLD_GOOD = 0.02
THRESHOLD_ALMOST = 0.05

def normalize_keypoints(landmarks):
    """Normalize pose keypoints to reduce variance due to position/scale."""
    landmarks = np.array(landmarks)
    landmarks = landmarks.reshape(-1, 4)
    # Normalize using the center of hips as reference
    if landmarks.shape[0] >= 24:
        hip_center = (landmarks[23][:3] + landmarks[24][:3]) / 2
        landmarks[:, :3] -= hip_center  # shift
    landmarks[:, :3] /= np.linalg.norm(landmarks[:, :3]) + 1e-8  # scale
    return landmarks.flatten()

def extract_keypoints_from_image(image):
    """Extract pose keypoints (132 values) from image."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    if results.pose_landmarks:
        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z, lm.visibility])
        landmarks = normalize_keypoints(landmarks)
        return landmarks
    return None

def check_exercise_quality(sequence):
    """Calculate reconstruction error and return feedback & confidence."""
    sequence_padded = pad_sequences([sequence], maxlen=100, dtype='float32', padding='post', truncating='post')
    pred = model.predict(sequence_padded, verbose=0)
    error = np.mean((sequence_padded - pred) ** 2)

    # Convert error to confidence (inverted scale)
    confidence = max(0.0, 1.0 - (error / THRESHOLD_ALMOST))

    if error < THRESHOLD_GOOD:
        feedback = "Good"
        status = "good"
    elif error < THRESHOLD_ALMOST:
        feedback = "Almost"
        status = "almost"
    else:
        feedback = "Not Correct"
        status = "poor"

    return feedback, confidence, error, status

@app.route('/analyze-pose', methods=['POST'])
def analyze_pose():
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = data['image']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Extract keypoints
        keypoints = extract_keypoints_from_image(image)
        
        if keypoints is None:
            return jsonify({
                'error': 'No pose detected in the image',
                'feedback': 'No pose detected',
                'confidence': 0.0,
                'status': 'no_pose'
            }), 400
        
        # Analyze exercise quality
        feedback, confidence, error, status = check_exercise_quality([keypoints])
        
        return jsonify({
            'feedback': feedback,
            'confidence': float(confidence),
            'reconstruction_error': float(error),
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'pose-detection'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)


