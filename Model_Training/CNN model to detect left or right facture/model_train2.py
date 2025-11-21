import os
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms, models
from PIL import Image
import torch.nn as nn

# ============ Dataset Loader ============ #
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

# ============ Transforms ============ #
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor()
])

# ============ Prepare Dataset & Split ============ #
full_dataset = LeftRightFromFilenameDataset(IMAGE_DIR, transform=transform)
train_size = int(0.8 * len(full_dataset))
val_size = len(full_dataset) - train_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

# ============ Model Setup ============ #
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 2)
model = model.to(device)

# Load previous weights
model.load_state_dict(torch.load('cnn_lr_from_filename.pth'))

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

# ============ Training Loop ============ #
for epoch in range(5, 10):  # Continue from epoch 6 to 10
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    train_acc = 100 * correct / total

    # ============ Validation ============ #
    model.eval()
    val_loss = 0
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_acc = 100 * val_correct / val_total
    scheduler.step()

    print(f"📦 Epoch {epoch+1}")
    print(f"   🔹 Train Loss: {total_loss:.4f} | Train Acc: {train_acc:.2f}%")
    print(f"   🔸 Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%\n")

# ============ Save Final Model ============ #
torch.save(model.state_dict(), 'cnn_lr_from_filename_v2.pth')
print("✅ Model saved as 'cnn_lr_from_filename_v2.pth'")
