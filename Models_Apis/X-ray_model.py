from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import tempfile
import os
import torch
import logging
import numpy as np
from ultralytics.nn.tasks import DetectionModel
import cv2
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image
from torchvision import models, transforms
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

torch.serialization.add_safe_globals([DetectionModel])
_original_torch_load = torch.load
def torch_load_unsafe(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)
torch.load = torch_load_unsafe

app = Flask(__name__)

# Add CORS support
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={r'/api/*': {'origins': cors_origins}})

# Load YOLO model for detection
model = YOLO('best.pt')

# Load a ResNet18 classifier for Grad-CAM (or use your custom classifier)
try:
    classifier = models.resnet18(pretrained=True)
    classifier.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    classifier.to(device)
    target_layer = classifier.layer4[-1]
    gradcam_available = True
    logger.info(f"✓ Grad-CAM classifier loaded on {device}")
except Exception as e:
    logger.warning(f"⚠️ Grad-CAM classifier failed to load: {str(e)}")
    gradcam_available = False
    device = None

HEATMAP_FOLDER = "static/heatmaps"
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

# ==================== Health Check ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        return jsonify({
            'status': 'ok',
            'service': 'xray-api',
            'version': '1.0.0',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'gradcam_available': gradcam_available
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'service': 'xray-api',
            'message': str(e)
        }), 500


def generate_gradcam(image_path, boxes):
    """
    Generate Grad-CAM heatmap for each detected bounding box
    
    Args:
        image_path: Path to the X-ray image
        boxes: List of bounding boxes from YOLO detection
    
    Returns:
        base64 encoded Grad-CAM image or None
    """
    if not gradcam_available or len(boxes) == 0:
        return None
    
    try:
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            logger.warning("Failed to read image for Grad-CAM")
            return None
        
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_copy = img_bgr.copy()
        
        # Process each detected box
        for box in boxes:
            x1, y1, x2, y2 = map(int, box[:4])
            
            # Extract crop
            crop = img_bgr[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            
            # Preprocess crop for classifier
            crop_resized = cv2.resize(crop, (224, 224))
            crop_rgb = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            
            # Convert to tensor
            transform = transforms.ToTensor()
            input_tensor = transform(crop_rgb).unsqueeze(0).to(device)
            
            # Apply Grad-CAM
            try:
                cam = GradCAM(model=classifier, target_layers=[target_layer])
                targets = [ClassifierOutputTarget(0)]  # Target class 0
                grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0, :]
                
                # Overlay Grad-CAM on crop
                cam_image = show_cam_on_image(crop_rgb, grayscale_cam, use_rgb=True)
                cam_image_bgr = cv2.cvtColor((cam_image * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
                
                # Resize to original box size
                cam_image_bgr = cv2.resize(cam_image_bgr, (x2 - x1, y2 - y1))
                
                # Place back on original image
                img_copy[y1:y2, x1:x2] = cam_image_bgr
                logger.info(f"✓ Grad-CAM applied to box: ({x1}, {y1}, {x2}, {y2})")
                
            except Exception as e:
                logger.warning(f"⚠️ Grad-CAM failed for box: {str(e)}")
                continue
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', img_copy)
        gradcam_base64 = base64.b64encode(buffer).decode('utf-8')
        logger.info("✓ Grad-CAM image encoded to base64")
        return gradcam_base64
        
    except Exception as e:
        logger.error(f"❌ Grad-CAM generation failed: {str(e)}")
        return None


@app.route('/detect-fracture', methods=['POST'])
def detect_fracture():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    
    # Confidence threshold - only accept detections >= 0.55
    CONFIDENCE_THRESHOLD = 0.55

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
        file.save(temp.name)
        image_path = temp.name

    # YOLO prediction
    results = model(image_path)

    labels = []
    boxes = []
    confidences = []
    
    for result in results:
        names = result.names
        for box in result.boxes:
            # Get confidence score for this detection
            confidence = float(box.conf[0])
            
            # Only include detections with confidence >= threshold
            if confidence >= CONFIDENCE_THRESHOLD:
                cls_id = int(box.cls[0])
                label = names[cls_id]
                labels.append(label)
                boxes.append(box.xyxy.cpu().numpy()[0])
                confidences.append(confidence)
                logger.info(f"✓ Detection accepted: {label} (confidence: {confidence:.2f})")
            else:
                cls_id = int(box.cls[0])
                label = names[cls_id]
                logger.info(f"⚠️ Detection filtered out: {label} (confidence: {confidence:.2f} < {CONFIDENCE_THRESHOLD})")

    # Generate Grad-CAM explainable image (only if detections passed threshold)
    gradcam_base64 = None
    if boxes:  # Only generate Grad-CAM if we have high-confidence detections
        try:
            gradcam_base64 = generate_gradcam(image_path, boxes)
            if gradcam_base64:
                logger.info("✓ Grad-CAM image generated successfully")
        except Exception as e:
            logger.warning(f"⚠️ Grad-CAM generation skipped: {str(e)}")

    os.remove(image_path)

    response = {}
    if labels:
        response['fracture_types'] = list(set(labels))
        response['detections_count'] = len(boxes)
        response['confidences'] = [f"{conf:.2f}" for conf in confidences]
    else:
        response['message'] = 'No fracture detected (all detections below confidence threshold of 0.55).'
        response['detections_count'] = 0

    # Return Grad-CAM heatmap if available
    if gradcam_base64:
        response['gradcam_image'] = f"data:image/jpeg;base64,{gradcam_base64}"
        response['explainability'] = f"Grad-CAM visualization of detected fractures (confidence threshold: {CONFIDENCE_THRESHOLD})"
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
