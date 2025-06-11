import torch
from .BaseModel import BaseModel
from transformers import UperNetForSemanticSegmentation, AutoImageProcessor
from PIL import Image
import numpy as np
import cv2
import os

class RoomEditor(BaseModel):
    def __init__(self):
        super().__init__()

        model_id = self.app_settings.SEGMENTATION_MODEL_ID
        model_name = model_id.split("/")[-1]

        base_dir = os.path.dirname(os.path.dirname(__file__)) #/src/
        models_weights_path =  os.path.join(base_dir, self.app_settings.MODELS_WEIGHTS_PATH)
        model_path = os.path.join(models_weights_path, model_name)
        print(model_path)
        self.seg_model = UperNetForSemanticSegmentation.from_pretrained(model_path)
        self.seg_processor = AutoImageProcessor.from_pretrained(model_path)

        self.seg_model.eval()
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
        h_new, s_new = target_hsv[0], target_hsv[1]

        H = H.astype(np.float32)
        S = S.astype(np.float32)
        V = V.astype(np.float32)
        V_new = 0.6 * V + 0.4 * V
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

    def replace_floor(self, image_pil, floor_mask, texture_path):
        if floor_mask is None or np.sum(floor_mask) == 0:
            return np.array(image_pil)

        image_np = np.array(image_pil)
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        mask_resized = cv2.resize(floor_mask, image_pil.size)
        binary_mask = (mask_resized * 255).astype(np.uint8)

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return image_np

        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        floor_contour = contours[0]
        epsilon = 0.02 * cv2.arcLength(floor_contour, True)
        approx = cv2.approxPolyDP(floor_contour, epsilon, True)
        if len(approx) != 4:
            x, y, w, h = cv2.boundingRect(floor_contour)
            approx = np.array([[[x, y]], [[x+w, y]], [[x+w, y+h]], [[x, y+h]]])

        dst_pts = np.array([pt[0] for pt in approx], dtype=np.float32)
        texture = cv2.imread(texture_path)
        h_tex, w_tex = texture.shape[:2]
        src_pts = np.array([[0, 0], [w_tex-1, 0], [w_tex-1, h_tex-1], [0, h_tex-1]], dtype=np.float32)
        H, _ = cv2.findHomography(src_pts, dst_pts)
        warped_texture = cv2.warpPerspective(texture, H, (image_np.shape[1], image_np.shape[0]))
        inverse_mask = cv2.bitwise_not(binary_mask)
        floor_part = cv2.bitwise_and(warped_texture, warped_texture, mask=binary_mask)
        background = cv2.bitwise_and(image_cv, image_cv, mask=inverse_mask)
        blended = cv2.add(floor_part, background)
        return cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)

    def preview_segmentation(self, image_pil, project_id: str,file_id: str):
        # if self.custom_masks is not None:
        #     return None  
        
        masks, segmenation = self.get_segmentation_masks(image_pil)
        seg_vis = self.create_seg_vis(segmenation)
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        save_dir = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH)
        project_dir = os.path.join(save_dir, project_id)
        
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
