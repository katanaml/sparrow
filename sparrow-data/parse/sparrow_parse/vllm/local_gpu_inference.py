import torch
from sparrow_parse.vllm.inference_base import ModelInference


class LocalGPUInference(ModelInference):
    def __init__(self, model, device='cuda'):
        self.model = model
        self.device = device
        self.model.to(self.device)

    def inference(self, input_data, apply_annotation=False, mode=None):
        self.model.eval()  # Set the model to evaluation mode
        with torch.no_grad():  # No need to calculate gradients
            input_tensor = torch.tensor(input_data).to(self.device)
            output = self.model(input_tensor)
        return output.cpu().numpy()  # Convert the output back to NumPy if necessary
