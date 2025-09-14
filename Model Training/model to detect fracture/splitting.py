import os
import shutil
import random

# Define dataset root directory
dataset_dir = os.getcwd()  # Uses the current working directory
# OR manually set it if the dataset is in a specific location
# dataset_dir = "/path/to/your/dataset"

image_dir = os.path.join(dataset_dir, "Processed_Images")
label_dir = os.path.join(dataset_dir, "Processed_Labels")

# Define split ratios
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1

split_dirs = ["train", "val", "test"]
for split in split_dirs:
    os.makedirs(os.path.join(dataset_dir, split, "images"), exist_ok=True)
    os.makedirs(os.path.join(dataset_dir, split, "labels"), exist_ok=True)

images = sorted([f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
random.shuffle(images)  

total_images = len(images)
train_count = int(total_images * train_ratio)
val_count = int(total_images * val_ratio)

train_images = images[:train_count]
val_images = images[train_count:train_count + val_count]
test_images = images[train_count + val_count:]

def move_files(file_list, split):
    for img_file in file_list:
        img_path = os.path.join(image_dir, img_file)
        label_path = os.path.join(label_dir, img_file.rsplit('.', 1)[0] + ".txt")  

        if os.path.exists(img_path):
            shutil.move(img_path, os.path.join(dataset_dir, split, "images", img_file))

        if os.path.exists(label_path):
            shutil.move(label_path, os.path.join(dataset_dir, split, "labels", os.path.basename(label_path)))

move_files(train_images, "train")
move_files(val_images, "val")
move_files(test_images, "test")

print("Dataset successfully split into train, val, and test sets!")
