import os
import onnxruntime as ort
import numpy as np

class MLModelRegistry:
    def __init__(self):
        self.models = {}
        self.registry_dir = "models/"
        os.makedirs(self.registry_dir, exist_ok=True)

    def load_model(self, model_name, version="latest"):
        model_path = os.path.join(self.registry_dir, f"{model_name}_{version}.onnx")
        if not os.path.exists(model_path):
            return None
        return ort.InferenceSession(model_path)

    def predict(self, model_name, input_data, version="latest"):
        session = self.load_model(model_name, version)
        if not session:
            raise ValueError(f"Model {model_name} not found")
        
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        result = session.run([output_name], {input_name: input_data})
        return result[0]

registry = MLModelRegistry()
