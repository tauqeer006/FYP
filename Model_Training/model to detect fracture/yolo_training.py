from ultralytics import YOLO
import multiprocessing

def main():
    # Load a model
    model = YOLO("yolov8n.pt")  # load a pretrained model
    
    # Train the model
    model.train(
        data="dataset.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        name='yolov8n_custom'
    )

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()