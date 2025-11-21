import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image, UnidentifiedImageError
import torch.nn as nn

IMAGE_DIR = 'dataset/train/images'

class LeftRightFromFilenameDataset(Dataset):
    def __init__(self, image_dir, transform=None):
        self.image_dir = image_dir
        self.transform = transform
        self.data = []
        self.skipped_files = 0  

        for img_name in os.listdir(image_dir):
            if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                if len(img_name) >= 24:
                    flag_char = img_name[23].upper()
                    if flag_char == 'L':
                        label = 0
                    elif flag_char == 'R':
                        label = 1
                    else:
                        continue

                    full_path = os.path.join(image_dir, img_name)
                    try:
                        with Image.open(full_path) as im:
                            im.verify()
                        self.data.append((full_path, label))
                    except Exception:
                        print(f"❌ Skipping corrupted file: {img_name}")
                        self.skipped_files += 1

        print(f"\n✅ Total usable images: {len(self.data)}")
        print(f"❌ Total corrupted or unreadable images skipped: {self.skipped_files}\n")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        image_path, label = self.data[idx]
        image = Image.open(image_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = LeftRightFromFilenameDataset(IMAGE_DIR, transform=transform)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 2)
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(5):
    model.train()
    total_loss = 0
    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"📦 Epoch {epoch+1} Loss: {total_loss:.4f}")

torch.save(model.state_dict(), 'cnn_lr_from_filename.pth')
print("\n✅ Model saved as 'cnn_lr_from_filename.pth'")
