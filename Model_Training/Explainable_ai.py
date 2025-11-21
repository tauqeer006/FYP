import torch
import cv2
import numpy as np
from torchvision import transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from ultralytics import YOLO
import matplotlib.pyplot as plt

# ---------- Load and Wrap YOLOv8 ----------
class YOLOv8Wrapper(torch.nn.Module):
    def __init__(self, yolo_model):
        super().__init__()
        self.model = yolo_model

    def forward(self, x):
        features = self.model.model[:-1](x)  # remove detection head
        out = features[-1]  # use last feature map
        out = torch.mean(out, dim=(2, 3))  # global average pooling for classification compatibility
        return out

# ---------- Load Trained Model ----------
device = 'cuda' if torch.cuda.is_available() else 'cpu'
yolo = YOLO("best1.pt")  # <-- Use your trained model
yolo.fuse()
yolo.to(device)

wrapped_model = YOLOv8Wrapper(yolo).to(device)
wrapped_model.eval()

# ---------- Set Target Layer for Grad-CAM ----------
target_layer = yolo.model.model[-2]  # last conv layer before detection head

# ---------- Load and Preprocess Image ----------
image_path = "sample.jpg"  # <-- Replace with your test image
img = cv2.imread(image_path)
img = cv2.resize(img, (640, 640))  # YOLO expects 640x640
rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
rgb_img = rgb_img.astype(np.float32) / 255.0

transform = transforms.Compose([
    transforms.ToTensor(),
])
input_tensor = transform(rgb_img).unsqueeze(0).to(device)

# ---------- Apply Grad-CAM ----------
cam = GradCAM(model=wrapped_model, target_layers=[target_layer])
grayscale_cam = cam(input_tensor=input_tensor)[0, :]

# ---------- Overlay CAM ----------
visualization = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)

# ---------- Display & Save ----------
plt.imshow(visualization)
plt.title("Grad-CAM on best1.pt")
plt.axis("off")
plt.show()

cv2.imwrite("gradcam_best1_result.jpg", cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))
