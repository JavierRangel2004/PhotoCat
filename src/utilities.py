from image_analysis import load_image, is_blurry, check_exposure
from object_detection import detect_objects

def process_image(path):
    image = load_image(path)
    if image is None:
        return None

    # Basic checks
    if is_blurry(image):
        rating = 1
        tags = ["blurry"]
        title = "Blurry Image"
        return rating, tags, title

    exposure = check_exposure(image)
    if exposure in ['under', 'over']:
        rating = 1
        tags = [exposure]
        title = f"{exposure.capitalize()} Image"
        return rating, tags, title

    # Object detection
    objects = detect_objects(image)
    tags = objects
    rating = 3
    if exposure == 'normal':
        rating += 1
    if objects:
        rating += 1
    rating = min(rating, 5)

    title = "A photo with objects" if objects else "Untitled"
    return rating, tags, title
