import os
import rawpy
import cv2
import numpy as np
import imageio

_RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf", ".pef", ".srw"}


def load_image(path):
    ext = os.path.splitext(path)[1].lower()

    # For standard image formats, use OpenCV directly (avoids rawpy error spam)
    if ext not in _RAW_EXTENSIONS:
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        if image is not None:
            return image
        print(f"Could not load image {path} with OpenCV.")
        return None

    # RAW formats: try rawpy first, fall back to OpenCV
    try:
        with rawpy.imread(path) as raw:
            rgb = raw.postprocess()
        image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return image
    except Exception as e:
        print(f"Error reading {path} with rawpy: {e}")
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        if image is not None:
            return image
        print(f"Could not load image {path} with fallback as well.")
        return None

def preprocess_image(image, apply_noise_reduction=False):
    # Normalize image: ensure dtype is uint8 and convert if needed
    if image.dtype != np.uint8:
        image = cv2.convertScaleAbs(image)
    # Optional noise reduction
    if apply_noise_reduction:
        image = cv2.medianBlur(image, 3)
    return image

def analyze_color_tone(image):
    # Compute average brightness and contrast
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    contrast = gray.std()  # standard deviation as a proxy for contrast
    return brightness, contrast

def is_blurry(image, threshold=100.0):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return lap_var < threshold

def check_exposure(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    # Define exposure thresholds (tweak these values)
    if mean_val < 50:  # underexposed
        return 'under'
    elif mean_val > 200: # overexposed
        return 'over'
    else:
        return 'normal'
