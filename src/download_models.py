import os
from helpers import get_settings
from utils import download_models
from transformers import (
    UperNetForSemanticSegmentation,
    AutoImageProcessor,
    DPTForDepthEstimation,
    DPTImageProcessor
)

if __name__ == '__main__':
    app_settiings = get_settings()
    model_ids = [
        app_settiings.SEGMENTATION_MODEL_ID,
        app_settiings.DEPTH_ESTIMATION_MODEL_ID
        ]
    base_dir = os.path.dirname(__file__)  #src
    save_path = os.path.join(base_dir, app_settiings.MODELS_WEIGHTS_PATH)

    model_paths = download_models(model_ids, save_path)

    seg_model = UperNetForSemanticSegmentation.from_pretrained(model_paths[0])
    seg_preprocessor = AutoImageProcessor.from_pretrained(model_paths[0], use_fast=False)
    
    depth_est_model = DPTForDepthEstimation.from_pretrained(model_paths[1])
    depth_est_preprocessor = DPTImageProcessor.from_pretrained(model_paths[1])
    
    print("downloaded successfully")



