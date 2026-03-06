import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

class ImageCaptioner:
    def __init__(self, model_name="Salesforce/blip-image-captioning-large", device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(
            model_name, torch_dtype=self.dtype
        ).to(self.device)

    def caption_image(self, image):
        # image: OpenCV image (BGR), convert to PIL (RGB)
        image_pil = Image.fromarray(image[:,:,::-1])
        inputs = self.processor(image_pil, return_tensors="pt")
        # Cast float tensors to match model dtype (avoids float32/float16 mismatch on CUDA)
        inputs = {
            k: v.to(device=self.device, dtype=self.dtype if v.dtype.is_floating_point else v.dtype)
            for k, v in inputs.items()
        }
        with torch.no_grad():
            out = self.model.generate(**inputs, max_length=50, num_beams=5, early_stopping=True)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption
