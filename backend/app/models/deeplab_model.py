import torch
from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large, DeepLabV3_MobileNet_V3_Large_Weights

class DeepLabModel:
    def __init__(self):
        self.device = torch.device('cpu')
        
        # Load pre-trained DeepLabV3 + MobileNetV3 model
        # Optimization: TorchScript / ONNX can go here
        weights = DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT
        self.model = deeplabv3_mobilenet_v3_large(weights=weights)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # For TorchScript (optional optimization as requested):
        # self.model = torch.jit.script(self.model)

    def predict(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """Runs the model on the CPU (optimized)."""
        with torch.no_grad():
            output = self.model(image_tensor)['out'][0]

        predictions = output.argmax(0)
        
        # Assume class > 0 is vegetation mask for this example
        veg_mask = (predictions > 0).byte() 
        return veg_mask

# Singleton instance
deep_lab_v3_model = DeepLabModel()
