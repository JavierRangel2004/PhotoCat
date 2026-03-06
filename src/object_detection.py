from ultralytics import YOLO

# Model loaded ONCE at module import — not per image call.
# This fixes the per-call bottleneck identified in Phase 0.
_MODEL_PATH = "yolov8l.pt"
_yolo_model = None


class ObjectDetector:
    """Wrapper that holds a single YOLO model instance."""

    def __init__(self, model_path=_MODEL_PATH):
        self.model = YOLO(model_path)

    def detect(self, image, conf=0.5):
        results = self.model(image, conf=conf)
        class_indices = (
            results[0].boxes.cls.tolist()
            if results and results[0].boxes.cls is not None
            else []
        )
        names = results[0].names
        return [names[int(i)] for i in class_indices]


def _get_default_model():
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = ObjectDetector()
    return _yolo_model


def detect_objects(image, conf=0.5):
    """Backward-compatible function. Uses the module-level singleton."""
    return _get_default_model().detect(image, conf=conf)
