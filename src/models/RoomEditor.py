import os
import cv2
import torch
import numpy as np
from PIL import Image
from .BaseModel import BaseModel
from transformers import (
    UperNetForSemanticSegmentation,
    AutoImageProcessor,
    DPTForDepthEstimation,
    DPTImageProcessor
)


class RoomEditor(BaseModel):
    def __init__(self):
        super().__init__()

        seg_model_id = self.app_settings.SEGMENTATION_MODEL_ID
        seg_model_name = seg_model_id.split("/")[-1]
        
        depth_est_model_id = self.app_settings.DEPTH_ESTIMATION_MODEL_ID
        depth_est_model_name = depth_est_model_id.split("/")[-1]

        base_dir = os.path.dirname(os.path.dirname(__file__)) #/src/
        models_weights_path =  os.path.join(base_dir, self.app_settings.MODELS_WEIGHTS_PATH)
        
        seg_model_path = os.path.join(models_weights_path, seg_model_name)
        depth_est_model_path = os.path.join(models_weights_path, depth_est_model_name)
        
        self.seg_model = UperNetForSemanticSegmentation.from_pretrained(seg_model_path)
        self.seg_processor = AutoImageProcessor.from_pretrained(seg_model_path, use_fast=False)
        
        self.depth_est_model = DPTForDepthEstimation.from_pretrained(depth_est_model_path)
        self.depth_est_preprocessor = DPTImageProcessor.from_pretrained(depth_est_model_path)

        self.seg_model.eval()
        self.depth_est_model.eval()
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.seg_model.to(self.device)
        self.depth_est_model.to(self.device)

        self.id2label = self.seg_model.config.id2label
        self.custom_masks = None
        
    def create_seg_vis(self, segmentation):
        color_map = np.zeros((*segmentation.shape, 3), dtype=np.uint8)
        for key, label in self.id2label.items():
            label = label.lower()
            if "wall" in label:
                color_map[segmentation == key] = self.app_settings.WALL_COLOR  # light pink
            elif "ceiling" in label:
                color_map[segmentation == key] = self.app_settings.CEILING_COLOR # light yellow
            elif "floor" in label:
                color_map[segmentation == key] = self.app_settings.FLOOR_COLOR # light green

        seg_vis = Image.fromarray(color_map)
        return seg_vis

    def set_custom_segmentation_mask(self, custom_mask, image_size):
        if not isinstance(custom_mask, np.ndarray):
            raise ValueError("Custom mask must be a NumPy array.")
        if custom_mask.ndim != 2:
            raise ValueError("Custom mask must be a 2D array.")

        resized_mask = cv2.resize(custom_mask.astype(np.uint8),
                                  image_size, interpolation=cv2.INTER_NEAREST)
        id2label = self.seg_model.config.id2label
        self.custom_masks = {}
        for key in id2label:
            label = id2label[key].lower()
            if "wall" in label or "ceiling" in label or "floor" in label:
                self.custom_masks[label] = (resized_mask == key).astype(np.uint8)

    def get_segmentation_masks(self, image_pil):
        inputs = self.seg_processor(images=image_pil, return_tensors="pt")
        with torch.no_grad():
            outputs = self.seg_model(**inputs)

        segmentation = torch.argmax(outputs.logits.squeeze(), dim=0).cpu().numpy()
        segmentation = cv2.resize(segmentation.astype(np.uint8),
                                  (image_pil.width, image_pil.height),
                                  interpolation=cv2.INTER_NEAREST)
        self.id2label = self.seg_model.config.id2label

        masks = dict()
        for key in self.id2label:
            label = self.id2label[key].lower()
            if "wall" in label or "ceiling" in label or "floor" in label:
                masks[label] = (segmentation == key).astype(np.uint8)

        
        return masks, segmentation

    def change_color(self, original_image, mask, target_rgb):
        if mask is None or np.sum(mask) == 0:
            return np.array(original_image)

        mask = mask.astype(np.float32)
        mask /= np.max(mask)
        image = np.array(original_image)
        target_bgr = target_rgb[::-1]

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        H, S, V = cv2.split(hsv)
        target_color_bgr = np.uint8([[target_bgr]])
        target_hsv = cv2.cvtColor(target_color_bgr, cv2.COLOR_BGR2HSV)[0][0]
        h_new, s_new, v_new = target_hsv

        H = H.astype(np.float32)
        S = S.astype(np.float32)
        V = V.astype(np.float32)
        V_new = 0.5 * V + 0.5 * v_new
        H = H * (1 - mask) + h_new * mask
        S = S * (1 - mask) + s_new * mask
        V = V * (1 - mask) + V_new * mask

        hsv_new = cv2.merge([
            H.astype(np.uint8),
            S.astype(np.uint8),
            V.astype(np.uint8)
        ])
        result = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2RGB)
        return result
    def get_depth_mask(self, image):
        depth_inputs = self.depth_est_preprocessor(images=image, return_tensors="pt")
        depth_inputs.to(self.device)
        with torch.no_grad():
            depth_outputs = self.depth_est_model(**depth_inputs)

        depth = depth_outputs.predicted_depth.squeeze().cpu().numpy()
        depth_resized = cv2.resize(depth, image.size)
        depth_resized = (depth_resized/depth_resized.max())*255
        depth_resized = np.uint8(depth_resized)
        
        return depth_resized
        
        
        
    def warp_texture_with_depth(self, image, texture, depth_map, mask):
        image = np.uint8(image)
        
        mask = np.uint8(mask/mask.max())
        depth_map = depth_map*mask
        
        x, y, w, h = cv2.boundingRect(mask)
        image_crop = image[y:y+h, x:x+w]
        depth_crop = depth_map[y:y+h, x:x+w]
        mask_crop = mask[y:y+h, x:x+w]
        texture = cv2.resize(texture, (w, h))

        x_grid, y_grid = np.meshgrid(np.arange(w), np.arange(h))
        z_normalized = depth_crop / (depth_crop.max() + 1e-6)  
        x_warped = x_grid * (0.5 + 0.5 * z_normalized)
        y_warped = y_grid * (0.5 + 0.5 * z_normalized)

        x_warped = np.clip(x_warped, 0, w-1).astype(np.float32)
        y_warped = np.clip(y_warped, 0, h-1).astype(np.float32)

        warped_texture = cv2.remap(
            texture,
            x_warped,
            y_warped,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )

        result = image.copy()
        result_crop = result[y:y+h, x:x+w]

        mask_3ch = np.stack([mask_crop]*3, axis=-1)

        result_crop[:] = warped_texture * mask_3ch + image_crop * (1 - mask_3ch)

        return result
    

    def preview_segmentation(self, image_pil, project_id: str,file_id: str):
        
        masks, segmenation = self.get_segmentation_masks(image_pil)
        seg_vis = self.create_seg_vis(segmenation)
        
        depth = self.get_depth_mask(image_pil)
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        save_dir = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH)
        project_dir = os.path.join(save_dir, project_id)
        
        depth_filename = f"{file_id}-DPTH.png"
        depth_path = os.path.join(project_dir, depth_filename)
        cv2.imwrite(depth_path, depth)
        
        seg_paths = dict()
        seg_colors = dict()
        
        for (label, mask) in masks.items():
            mask_filename = f"{file_id}-MSK:{label}.png"
            mask_path = os.path.join(project_dir, mask_filename)
            seg_paths[label] = mask_path
            if "wall" in label:
                seg_colors[label] = self.app_settings.WALL_COLOR  # light pink
            elif "ceiling" in label:
                seg_colors[label] = self.app_settings.CEILING_COLOR # light yellow
            elif "floor" in label:
                seg_colors[label] = self.app_settings.FLOOR_COLOR # light green
            mask = mask*255
            cv2.imwrite(mask_path, mask)
        
        seg_vis_filename = f"{file_id}-seg_vis.png"
        seg_vis_path = os.path.join(project_dir, seg_vis_filename)
        seg_vis.save(seg_vis_path)
        
        return seg_vis_path, seg_paths, seg_colors

    def process(self, image_pil, color_wall=None, color_ceiling=None, floor_texture=None):
        if self.custom_masks is not None:
            masks = self.custom_masks
            seg_vis = None
        else:
            masks, seg_vis = self.get_segmentation_masks(image_pil)

        image_result = np.array(image_pil)

        if color_wall:
            image_result = self.change_color(Image.fromarray(image_result), masks.get("wall"), color_wall)

        if color_ceiling:
            image_result = self.change_color(Image.fromarray(image_result), masks.get("ceiling"), color_ceiling)

        if floor_texture:
            image_result = self.replace_floor(Image.fromarray(image_result), masks.get("floor"), floor_texture)

        return Image.fromarray(image_result), seg_vis
