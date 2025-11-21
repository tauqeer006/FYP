from flask import Flask, request, jsonify
from ultralytics import YOLO
import tempfile
import os
import torch
from ultralytics.nn.tasks import DetectionModel


torch.serialization.add_safe_globals([DetectionModel])
_original_torch_load = torch.load
def torch_load_unsafe(*args, **kwargs):
    kwargs["weights_only"] = False  # Force it to allow older YOLO checkpoints
    return _original_torch_load(*args, **kwargs)
torch.load = torch_load_unsafe


app = Flask(__name__)

model = YOLO('best.pt')


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
