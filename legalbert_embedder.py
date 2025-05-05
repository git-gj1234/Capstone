from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from typing import List

class LegalBERTEmbedder:
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        # Check if CUDA is available and set device accordingly
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)  # Move model to GPU if available
        except Exception as e:
            print(f"Error loading model or tokenizer: {e}")
            raise

    def encode(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt")
                inputs = {key: value.to(self.device) for key, value in inputs.items()}  # Move inputs to GPU if available
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    pooled = outputs.last_hidden_state.mean(dim=1)  # Mean pooling
                    embeddings.append(pooled.cpu().numpy())  # Move back to CPU and convert to numpy
            except Exception as e:
                print(f"Error processing batch {i//batch_size}: {e}")
                continue

        return np.vstack(embeddings)
