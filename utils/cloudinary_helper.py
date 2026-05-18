# utils/cloudinary_helper.py
import cloudinary.uploader
import cloudinary.api
from werkzeug.datastructures import FileStorage

def upload_expense_image(file: FileStorage) -> dict:
    """
    Upload ảnh lên Cloudinary, trả về dict chứa url và public_id.
    Có thể tự động resize, nén để tiết kiệm dung lượng.
    """
    result = cloudinary.uploader.upload(
        file,
        folder = "expense_images",          # thư mục trên Cloudinary
        transformation = [
            {"width": 1200, "height": 1200, "crop": "limit"}, # giới hạn kích thước
            {"quality": "auto"}                               # nén tự động
        ]
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }

def delete_expense_image(public_id: str) -> bool:
    """Xoá ảnh khỏi Cloudinary, trả về True nếu thành công."""
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        print(f"Lỗi xoá Cloudinary: {e}")
        return False