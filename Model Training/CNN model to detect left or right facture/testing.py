import requests
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from io import BytesIO

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select an image")

if not file_path:
    print("No file selected.")
    exit()

image = Image.open(file_path).convert("RGB")
image = image.resize((640, 640))

buffer = BytesIO()
image.save(buffer, format='JPEG')
buffer.seek(0)

url = 'http://127.0.0.1:5000/predict-lr'
files = {'image': ('resized.jpg', buffer, 'image/jpeg')}
response = requests.post(url, files=files)

if response.ok:
    print("✅ Prediction:", response.json()['prediction'])
else:
    print("❌ Error:", response.text)
