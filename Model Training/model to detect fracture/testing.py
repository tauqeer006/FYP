import requests
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

image_path = filedialog.askopenfilename(
    title="Select an Image for Fracture Detection",
    filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
)

if not image_path:
    print("❌ No image selected.")
    exit()

# API endpoint
url = 'http://127.0.0.1:5000/detect-fracture'

# Send image to Flask API
with open(image_path, 'rb') as img_file:
    files = {'image': img_file}
    response = requests.post(url, files=files)

# Handle response
if response.status_code == 200:
    print("✅ Fracture Detection Result:")
    print(response.json())
else:
    print("❌ Error:", response.status_code, response.text)
