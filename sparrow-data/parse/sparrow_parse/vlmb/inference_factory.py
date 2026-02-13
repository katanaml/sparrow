class InferenceFactory:
    def __init__(self, config):
        self.config = config

    def get_inference_instance(self):
        if self.config["method"] == "huggingface":
            from sparrow_parse.vlmb.huggingface_inference import HuggingFaceInference
            return HuggingFaceInference(hf_space=self.config["hf_space"], hf_token=self.config["hf_token"])
        elif self.config["method"] == "local_gpu":
            from sparrow_parse.vlmb.local_gpu_inference import LocalGPUInference
            model = self._load_local_model()  # Replace with actual model loading logic
            return LocalGPUInference(model=model, device=self.config.get("device", "cuda"))
        elif self.config["method"] == "mlx":
            from sparrow_parse.vlmb.mlx_inference import MLXInference
            return MLXInference(model_name=self.config["model_name"])
        elif self.config["method"] == "ollama":
            from sparrow_parse.vlmb.ollama_inference import OllamaInference
            return OllamaInference(model_name=self.config["model_name"])
        elif self.config["method"] == "vllm":
            from sparrow_parse.vlmb.vllm_inference import VLLMInference
            return VLLMInference(model_name=self.config["model_name"])
        else:
            raise ValueError(f"Unknown method: {self.config['method']}")

    def _load_local_model(self):
        # Example: Load a PyTorch model (replace with actual loading code)
        # model = torch.load('model.pth')
        # return model
        raise NotImplementedError("Model loading logic not implemented")
