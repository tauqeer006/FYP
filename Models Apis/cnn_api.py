from flask import Flask, request, jsonify
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
from io import BytesIO

app = Flask(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load('cnn_lr_from_filename_v2.pth', map_location=device))
model = model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

label_map = {0: 'Left (L)', 1: 'Right (R)'}

@app.route('/predict-lr', methods=['POST'])
def predict_lr():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    try:
        image = Image.open(image_file).convert("RGB")
        image = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(image)
            _, predicted = torch.max(outputs, 1)

        prediction = label_map[predicted.item()]
        return jsonify({'prediction': prediction})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
