from enum import Enum
from helpers import get_settings


class ResponseEnum(Enum):

    app_settings = get_settings()
    
    
    FILE_TYPE_NOT_SUPPORTED_ENG = "File Type Not Supported: \n Supported types: mp4, mpeg , x-msvideo, webm, x-matroska, webm, ogg, quicktime, x-flv"
    FILE_SIZE_EXCEEDED_ENG = f"File Size Exceeded: \n Maximum Allowed Size: {app_settings.FILE_ALLOWED_SIZE}MB"
    FILE_UPLOADED_SUCCESSFULLY_ENG = "File Uploaded Successfuly"
    
    PROJECT_DOES_NOT_EXIST_ENG = "Project does not exits, The ID you entered is not valid or has been deleted."
    FILE_DOES_NOT_EXIST_ENG = "File does not exists, The File ID you entered is not valid or has been deleted."
    PROJECT_FOUND_SUCCESSFULLY_ENG = "Project found successfully."
    FILE_FOUND_SUCCESSFULLY_ENG = "File found successfully."

    FILE_TYPE_NOT_SUPPORTED_AR = "نوع الملف غير مدعوم:\nالأنواع المدعومة: mp4، mpeg، x-msvideo، webm، x-matroska، ogg، quicktime، x-flv"
    FILE_SIZE_EXCEEDED_AR = f"تجاوز حجم الملف:\nالحد الأقصى المسموح به: {app_settings.FILE_ALLOWED_SIZE} ميجابايت"
    FILE_UPLOADED_SUCCESSFULLY_AR = "تم تحميل الملف بنجاح"
    PROJECT_DOES_NOT_EXIST_AR = "التصميم غير موجود، الرقم التعريفي الذي أدخلته غير صالح أو تم حذفه."
    FILE_DOES_NOT_EXIST_AR = "الملف غير موجود، الرقم التعريفي للملف الذي أدخلته غير صالح أو تم حذفه."
    PROJECT_FOUND_SUCCESSFULLY_AR = "تم العثور على التصميم بنجاح."
    FILE_FOUND_SUCCESSFULLY_AR = "تم العثور على الملف بنجاح."
