from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import tempfile
import os
import torch
import logging
from ultralytics.nn.tasks import DetectionModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

torch.serialization.add_safe_globals([DetectionModel])
_original_torch_load = torch.load
def torch_load_unsafe(*args, **kwargs):
    kwargs["weights_only"] = False  # Force it to allow older YOLO checkpoints
    return _original_torch_load(*args, **kwargs)
torch.load = torch_load_unsafe


app = Flask(__name__)

# Add CORS support
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={r'/api/*': {'origins': cors_origins}})

model = YOLO('best.pt')


# ==================== Health Check ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
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

    results = model(image_path)

    labels = []
    for result in results:
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            labels.append(names[cls_id])

    os.remove(image_path)

    if not labels:
        return jsonify({'message': 'No fracture detected.'})
    else:
        return jsonify({'fracture_types': list(set(labels))})
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002 , debug=True)
