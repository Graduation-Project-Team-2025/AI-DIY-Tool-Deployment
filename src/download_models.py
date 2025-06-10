import os
from helpers import get_settings
from utils import download_models
from transformers import UperNetForSemanticSegmentation, AutoImageProcessor

if __name__ == '__main__':
    app_settiings = get_settings()
    model_ids = [app_settiings.SEGMENTATION_MODEL_ID]
    base_dir = os.path.dirname(__file__)
    save_path = os.path.join(base_dir, app_settiings.MODELS_WEIGHTS_PATH)

    model_paths = download_models(model_ids, save_path)

    for model_path in model_paths:
        seg_model = UperNetForSemanticSegmentation.from_pretrained(model_path)
        seg_preprocessor = AutoImageProcessor.from_pretrained(model_path)
    
    print("downloaded successfully")



