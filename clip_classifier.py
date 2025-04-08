import torch
import torchvision.transforms as T
from PIL import Image
import open_clip

class CLIPNudeChecker:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        self.model = model.to(self.device)
        self.preprocess = preprocess
        self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
        self.prompts = [
            "a nude photo",
            "a person in lingerie",
            "a person fully clothed"
        ]
        self.tokenized = self.tokenizer(self.prompts).to(self.device)

    def classify(self, image_path):
        image = self.preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
            text_features = self.model.encode_text(self.tokenized)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1).cpu().numpy()[0]

        return dict(zip(self.prompts, similarity))
