# src/ocr.py
import os
import pytesseract
from PIL import Image

class OCRDependencyError(Exception):
    """Exception raised when Tesseract OCR binary is missing."""
    pass

def ocr_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.
    Raises OCRDependencyError if tesseract is not installed.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")
        
    try:
        # Open image using Pillow
        img = Image.open(image_path)
        # Perform OCR
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        raise OCRDependencyError(
            "Tesseract-OCR binary was not found. Please install it using your package manager "
            "(e.g., 'sudo apt-get install tesseract-ocr') and ensure it is in your system PATH."
        )
    except Exception as e:
        raise RuntimeError(f"An error occurred during OCR text extraction: {str(e)}")
