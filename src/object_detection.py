from ultralytics import YOLO

def detect_objects(image):
    # Load YOLO model (ensure yolov8s.pt is a valid model file)
    model = YOLO("yolov8l.pt") 
    results = model(image, conf=0.5)
    class_indices = results[0].boxes.cls.tolist() if results and results[0].boxes.cls is not None else []
    names = results[0].names
    detected_names = [names[int(i)] for i in class_indices]
    return detected_names
