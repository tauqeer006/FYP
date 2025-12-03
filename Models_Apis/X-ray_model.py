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
from pytorch_grad_cam.utils.image import show_cam_on_image, preprocess_image

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

model = YOLO('best.pt')

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
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'service': 'xray-api',
            'message': str(e)
        }), 500

@app.route('/detect-fracture', methods=['POST'])
def detect_fracture():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
        file.save(temp.name)
        image_path = temp.name

    # YOLO prediction
    results = model(image_path)

    labels = []
    for result in results:
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            labels.append(names[cls_id])

    # ---------------- Explainable AI: Saliency Map ----------------
    saliency_map_base64 = None
    
    try:
        img_bgr = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Generate saliency map using Sobel edge detection
        # This shows regions of high gradient (important features)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Compute gradients using Sobel
        sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=5)
        sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=5)
        
        # Magnitude of gradients
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # Normalize to 0-1
        magnitude = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min() + 1e-8)
        
        # Apply Gaussian blur for smoothing
        saliency = cv2.GaussianBlur(magnitude, (21, 21), 0)
        
        # Normalize again
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
        
        # Apply colormap
        saliency_colored = cv2.applyColorMap((saliency * 255).astype(np.uint8), cv2.COLORMAP_JET)
        
        # Blend with original image
        heatmap = cv2.addWeighted(img_bgr, 0.6, saliency_colored, 0.4, 0)
        
        # Encode heatmap to base64 instead of saving to file
        import base64
        _, buffer = cv2.imencode('.jpg', heatmap)
        saliency_map_base64 = base64.b64encode(buffer).decode('utf-8')
        logger.info(f"Saliency map generated and encoded to base64")
        
    except Exception as e:
        logger.warning(f"Saliency map generation failed: {str(e)}")


    os.remove(image_path)

    response = {}
    if labels:
        response['fracture_types'] = list(set(labels))
    else:
        response['message'] = 'No fracture detected.'

    if saliency_map_base64:
        response['saliency_map_url'] = f"data:image/jpeg;base64,{saliency_map_base64}"

    return jsonify(response)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
