import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

class ImageCaptioner:
    def __init__(self, model_name="Salesforce/blip-image-captioning-large", device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name).to(self.device)

    def caption_image(self, image):
        # image: OpenCV image (BGR), convert to PIL (RGB)
        image_pil = Image.fromarray(image[:,:,::-1])
        inputs = self.processor(image_pil, return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, max_length=50, num_beams=5, early_stopping=True)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption
