import os
import cv2
import numpy as np
from multiprocessing import Pool, cpu_count
import pytesseract
import nltk
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
import string

# Ensure NLTK data is downloaded in your environment:
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

from image_analysis import load_image, is_blurry, check_exposure, preprocess_image, analyze_color_tone
from object_detection import detect_objects
from metadata_writer import write_xmp_sidecar
from image_captioning import ImageCaptioner

#####################
# Configuration Flags
#####################
ENABLE_BLUR_CHECK = True
ENABLE_EXPOSURE_CHECK = True
ENABLE_OBJECT_DETECTION = True
ENABLE_RATING_LOGIC = True
ENABLE_XMP_WRITING = True

captioner = ImageCaptioner()

#####################
# Helper Functions
#####################

def compute_composition_rating(image, objects):
    # Analyze if main objects are near rule-of-thirds lines:
    # If YOLO gives bounding boxes, we could get them. For now, assume objects is a list of class names only.
    # Without bounding boxes, we approximate composition rating by presence of multiple distinct objects and variety.
    # A placeholder: More objects = more interesting composition, up to a point
    # If we had boxes: we’d check their centroid positions against rule-of-thirds lines.
    comp_rating = 0
    if len(objects) == 0:
        comp_rating = 1
    elif len(objects) == 1:
        comp_rating = 2
    else:
        comp_rating = 3  # multiple objects add visual interest
    
    # Could add more heuristics if bounding boxes were available.
    return comp_rating

def compute_rating(is_blur, exposure, objects_detected, composition_score):
    # Base rating: start from composition_score (1-3)
    rating = composition_score
    # Adjust for technical aspects
    if is_blur:
        rating -= 1
    if exposure in ['under', 'over']:
        rating -= 1
    else:
        rating += 1  # good exposure adds to rating

    # Ensure rating between 1 and 5
    rating = max(1, min(rating, 5))
    return rating

def basic_color_name(rgb):
    r, g, b = rgb
    hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
    h, s, v = hsv
    if s < 50 and v > 200:
        return "white"
    if v < 50:
        return "black"
    if s < 50 and v < 200:
        return "gray"
    if h < 15 or h > 165:
        return "red"
    elif h < 35:
        return "orange"
    elif h < 85:
        return "green"
    elif h < 125:
        return "blue"
    elif h < 165:
        return "purple"
    return "colorful"

def extract_top_colors(image, top_n=3):
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_small = cv2.resize(img_rgb, (100, 100))
    data = img_small.reshape(-1, 3)
    data = np.float32(data)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = top_n
    _, labels, centers = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    centers = np.uint8(centers)
    counts = np.bincount(labels.flatten())
    sorted_idx = np.argsort(counts)[::-1]
    top_colors = centers[sorted_idx]

    named_colors = []
    for c in top_colors:
        color_name = basic_color_name(c)
        if color_name not in named_colors:
            named_colors.append(color_name)
    return named_colors

def detect_mood(image):
    brightness, contrast = analyze_color_tone(image)
    # More nuanced mood detection:
    # bright & low contrast = serene, bright & high contrast = vibrant, dark & low contrast = muted, dark & high contrast = dramatic
    if brightness > 150 and contrast < 50:
        return "serene"
    elif brightness > 150 and contrast >= 50:
        return "vibrant"
    elif brightness < 80 and contrast < 50:
        return "muted"
    elif brightness < 80 and contrast >= 50:
        return "dramatic"
    else:
        return "calm"

def ocr_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    text = pytesseract.image_to_string(gray)
    return text.lower()

def analyze_scene(objects, ocr_result):
    beverage_words = ["can", "bottle", "drink", "beverage"]
    brand_words = ["mamitas", "mandarina", "coca", "pepsi"]

    lower_objects = [obj.lower() for obj in objects]
    has_beverage = any(obj in lower_objects for obj in beverage_words)

    if not has_beverage:
        for bw in beverage_words:
            if bw in ocr_result:
                has_beverage = True
                break

    identified_brand = None
    for bw in brand_words:
        if bw in ocr_result:
            identified_brand = bw
            break

    return has_beverage, identified_brand

def caption_to_tags(caption):
    # Extract nouns and adjectives from the caption to generate tags
    words = word_tokenize(caption.lower())
    words = [w for w in words if w not in set(stopwords.words('english')) and w not in string.punctuation]
    pos_tags = pos_tag(words)
    # Consider nouns and adjectives as tags
    tags = [w for w, pos in pos_tags if pos.startswith('NN') or pos.startswith('JJ')]
    return list(set(tags))  # unique

def generate_tags_from_all(objects_detected, image, has_beverage, identified_brand, caption):
    tags = set()

    # From objects
    tags.update(obj.lower() for obj in objects_detected)

    # From colors and mood
    top_colors = extract_top_colors(image, top_n=3)
    tags.update(top_colors)
    mood_tag = detect_mood(image)
    tags.add(mood_tag)

    # From beverage/brand
    if has_beverage:
        tags.add("beverage")
        if identified_brand:
            tags.add(identified_brand)

    # From caption (nouns/adjectives)
    caption_tags = caption_to_tags(caption)
    tags.update(caption_tags)

    return list(tags)

def refine_title(caption, objects_detected, has_beverage, identified_brand):
    # Use the caption as the basis for the title.  
    # If beverage and brand are known, integrate them.
    # If a person is detected, try to mention it.
    # The caption should already be descriptive. Just ensure it starts with a capital letter and is a proper sentence.
    # Example: caption: "a person holding an orange can on a couch"
    # Refine to: "A person holding an orange beverage can (Mamitas) on a couch."
    
    title = caption.strip()
    if not title.endswith('.'):
        title += '.'
    title = title[0].upper() + title[1:]  # capitalize first letter

    # Add brand detail if known
    if has_beverage and identified_brand and identified_brand not in title.lower():
        # Insert brand detail after "beverage can" or similar
        if "beverage can" in title.lower():
            title = title.replace("beverage can", f"{identified_brand.capitalize()} beverage can")
        elif "can" in title.lower():
            title = title.replace("can", f"{identified_brand.capitalize()} can")

    return title

def process_image(img_path):
    print(f"Processing image: {img_path}")
    image = load_image(img_path)
    if image is None:
        print(f"Skipping {img_path} due to load failure.")
        return None, None, None

    image = preprocess_image(image, apply_noise_reduction=True)

    if ENABLE_BLUR_CHECK:
        is_image_blurry = is_blurry(image)
    else:
        is_image_blurry = False

    if ENABLE_EXPOSURE_CHECK:
        exposure = check_exposure(image)
    else:
        exposure = 'normal'

    objects_detected = []
    if ENABLE_OBJECT_DETECTION:
        objects_detected = detect_objects(image)

    # OCR to detect possible text (brand, etc.)
    ocr_result = ocr_text(image)

    # Scene analysis (beverage detection, brand)
    has_beverage, identified_brand = analyze_scene(objects_detected, ocr_result)

    # Use image captioning model (BLIP)
    caption = captioner.caption_image(image)

    # Compute a composition score (simple heuristic)
    composition_score = compute_composition_rating(image, objects_detected)

    # Compute rating
    rating = compute_rating(is_image_blurry, exposure, objects_detected, composition_score)

    # Generate tags from all sources
    tags = generate_tags_from_all(objects_detected, image, has_beverage, identified_brand, caption)

    # Refine the caption into a title
    title = refine_title(caption, objects_detected, has_beverage, identified_brand)

    print(f"Finished processing {img_path}: Rating={rating}, Tags={tags}, Title='{title}'")
    return rating, tags, title

def process_and_write(img_path):
    rating, tags, title = process_image(img_path)
    if rating is not None and ENABLE_XMP_WRITING:
        write_xmp_sidecar(img_path, rating, tags, title)
        return (img_path, rating, tags, title)
    return (img_path, None, None, None)

def main():
    input_dir = "images"
    print(f"Processing images in {input_dir}")
    image_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(('.cr2','.cr3','.jpg','.jpeg','.png','.tiff'))]

    num_workers = min(cpu_count(), 8)  # Use up to 8 cores
    with Pool(num_workers) as p:
        results = p.map(process_and_write, image_files)

    for res in results:
        img_path, rating, tags, title = res
        if rating is not None:
            print(f"Processed {img_path}: Rating={rating}, Tags={tags}, Title='{title}'")
        else:
            print(f"Skipped {img_path}")

if __name__ == "__main__":
    main()
