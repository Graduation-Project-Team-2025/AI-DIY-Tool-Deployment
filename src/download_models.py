import os
from helpers import get_settings
from utils import download_models

if __name__ == '__main__':
    app_settiings = get_settings()
    model_ids = [app_settiings.SEGMENTATION_MODEL_ID]
    base_dir = os.path.dirname(__file__)
    save_path = os.path.join(base_dir, app_settiings.MODELS_WEIGHTS_PATH)

    download_models(model_ids, save_path)

