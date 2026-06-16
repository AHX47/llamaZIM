import os
import yaml
from llama_cpp import Llama

class ModelManager:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.models_dir = self.config['models_dir']
        self.llm = None

    def load_model(self, model_filename):
        model_path = os.path.join(self.models_dir, model_filename)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        print(f"Loading model: {model_filename} on CPU...")
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=self.config.get('llm_n_gpu_layers', 0),
            n_batch=self.config.get('llm_n_batch', 512),
            n_ctx=self.config.get('llm_n_ctx', 2048),
            verbose=self.config.get('llm_verbose', False)
        )
        print("Model loaded successfully.")

    def generate_response(self, prompt, stream=True):
        if not self.llm:
            raise Exception("Model not loaded. Call load_model() first.")

        if stream:
            return self.llm(
                prompt,
                max_tokens=self.config.get('max_tokens', 512),
                stream=True
            )
        else:
            return self.llm(
                prompt,
                max_tokens=self.config.get('max_tokens', 512),
                stream=False
            )

    def chat_completion(self, messages, stream=True):
        if not self.llm:
            raise Exception("Model not loaded. Call load_model() first.")
        
        return self.llm.create_chat_completion(
            messages=messages,
            max_tokens=self.config.get('max_tokens', 512),
            stream=stream
        )
