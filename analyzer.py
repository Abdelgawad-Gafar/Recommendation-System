import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from moviepy import VideoFileClip
from PIL import Image
import logging

logger = logging.getLogger("Analyzer")

class ReelAnalyzer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading CLIP model on {self.device}...")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    def process_video(self, video_path, context_text):
        logger.info("Starting visual and text analysis using CLIP...")
        clip = VideoFileClip(video_path)
        
        frames = [Image.fromarray(clip.get_frame(t)) for t in np.arange(0, clip.duration, 2)]
        inputs = self.clip_processor(images=frames, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            visual_emb = torch.mean(self.clip_model.get_image_features(**inputs), dim=0).cpu().numpy()
        
        inputs_text = self.clip_processor(text=[context_text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            text_emb = self.clip_model.get_text_features(**inputs_text).squeeze(0).cpu().numpy()

        clip.close()
        final_vector = (visual_emb * 0.6 + text_emb * 0.4)
        return final_vector / np.linalg.norm(final_vector)