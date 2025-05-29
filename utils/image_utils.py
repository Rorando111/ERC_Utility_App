import cv2
import numpy as np
from PIL import Image, ImageEnhance
from PyQt5.QtGui import QImage

def preprocess_image(pil_image):
    # Convert PIL to OpenCV format
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Resize for consistency
    height, width = gray.shape
    if width < 1000:
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_LINEAR)

    # Increase contrast
    pil_gray = Image.fromarray(gray)
    enhancer = ImageEnhance.Contrast(pil_gray)
    enhanced = enhancer.enhance(2.0)

    # Convert back to numpy array
    enhanced_np = np.array(enhanced)

    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        enhanced_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )

    # Optional: crop only the bottom-right quadrant
    h, w = thresh.shape
    cropped = thresh[int(h * 0.7):, int(w * 0.5):]  # Bottom right corner

    # Return as PIL Image
    return Image.fromarray(cropped)

def pil_image_to_qimage(pil_image):
    """Convert a PIL.Image to QImage"""
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    data = pil_image.tobytes("raw", "RGB")
    width, height = pil_image.size
    qimage = QImage(data, width, height, QImage.Format_RGB888)
    return qimage

def deskew_image(pil_image: Image.Image) -> Image.Image:
    img = np.array(pil_image.convert("L"))
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary = cv2.bitwise_not(binary)

    coords = np.column_stack(np.where(binary > 0))
    if coords.shape[0] == 0:
        return pil_image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated_cv = cv2.warpAffine(np.array(pil_image), M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    return Image.fromarray(rotated_cv)

