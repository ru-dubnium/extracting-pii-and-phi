# tests/test_extractor.py
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from src.regex_extractor import regex_extract
from src.merger import merge_entities
from src.risk import compute_risk
from src.leakage import detect_leakage
from src.ocr import ocr_image, OCRDependencyError
from src.extractor import HybridExtractor


def test_regex_extractor():
    text = "Send mail to support@example.com or call 555-123-4567. My DOB is 1990-01-15, and ID is AB12345678."
    entities = regex_extract(text)
    
    types = {e['type'] for e in entities}
    assert "EMAIL" in types
    assert "PHONE" in types
    assert "DATE_OF_BIRTH" in types
    assert "HEALTH_INSURANCE_ID" in types
    
    # Check values
    values = {e['value'] for e in entities}
    assert "support@example.com" in values
    assert "555-123-4567" in values
    assert "1990-01-15" in values
    assert "AB12345678" in values


def test_merger_deduplication():
    # 1. Exact duplicates: Regex should win
    regex_list = [{
        "type": "EMAIL",
        "value": "alice@example.com",
        "confidence": 1.0,
        "start": 0,
        "end": 17,
        "source": "regex"
    }]
    llm_list = [{
        "type": "EMAIL",
        "value": "alice@example.com",
        "confidence": 0.9,
        "start": 0,
        "end": 17,
        "source": "llm"
    }]
    
    merged = merge_entities(regex_list, llm_list)
    assert len(merged) == 1
    assert merged[0]['source'] == 'regex'
    assert merged[0]['confidence'] == 1.0


def test_merger_overlap_resolution():
    # 2. Overlapping spans: Longest match wins
    # Example: "Main St, Springfield, IL" vs "123 Main St, Springfield, IL"
    regex_list = [{
        "type": "ADDRESS",
        "value": "Main St, Springfield, IL",
        "confidence": 0.9,
        "start": 4,
        "end": 28,
        "source": "regex"
    }]
    llm_list = [{
        "type": "ADDRESS",
        "value": "123 Main St, Springfield, IL",
        "confidence": 0.8,
        "start": 0,
        "end": 28,
        "source": "llm"
    }]
    
    merged = merge_entities(regex_list, llm_list)
    assert len(merged) == 1
    assert merged[0]['value'] == "123 Main St, Springfield, IL"
    
    # 3. Overlapping spans: Equal length, higher confidence wins
    entity_a = {
        "type": "ADDRESS",
        "value": "123 Main St",
        "confidence": 0.9,
        "start": 0,
        "end": 11,
        "source": "llm"
    }
    entity_b = {
        "type": "ADDRESS",
        "value": "123 Main St",
        "confidence": 0.8,
        "start": 0,
        "end": 11,
        "source": "heuristic"
    }
    merged_eq = merge_entities([entity_a], [entity_b])
    assert len(merged_eq) == 1
    assert merged_eq[0]['confidence'] == 0.9


def test_risk_scoring():
    # HIGH Risk
    high_entities = [{"type": "MEDICAL_CONDITION", "value": "diabetes"}]
    assert compute_risk(high_entities) == "HIGH"
    
    # MEDIUM Risk
    med_entities = [{"type": "EMAIL", "value": "test@test.com"}]
    assert compute_risk(med_entities) == "MEDIUM"
    
    # LOW Risk
    low_entities = []
    assert compute_risk(low_entities) == "LOW"


def test_leakage_detection():
    input_entities = [
        {"type": "EMAIL", "value": "alice@example.com"},
        {"type": "MEDICATION", "value": "insulin"}
    ]
    output_entities = [
        {"type": "EMAIL", "value": "alice@example.com"}
    ]
    
    leaked = detect_leakage(input_entities, output_entities)
    assert len(leaked) == 1
    assert leaked[0]['value'] == "alice@example.com"
    
    # No leakage
    output_entities_safe = [
        {"type": "EMAIL", "value": "different@example.com"}
    ]
    assert len(detect_leakage(input_entities, output_entities_safe)) == 0


@patch('pytesseract.image_to_string')
@patch('os.path.exists')
@patch('PIL.Image.open')
def test_ocr_success(mock_open, mock_exists, mock_image_to_string):
    mock_exists.return_value = True
    mock_image_to_string.return_value = "Test OCR content with email@test.com"
    
    text = ocr_image("dummy_path.png")
    assert text == "Test OCR content with email@test.com"
    mock_image_to_string.assert_called_once()


@patch('pytesseract.image_to_string')
@patch('os.path.exists')
@patch('PIL.Image.open')
def test_ocr_missing_binary(mock_open, mock_exists, mock_image_to_string):
    import pytesseract
    mock_exists.return_value = True
    mock_image_to_string.side_effect = pytesseract.TesseractNotFoundError()
    
    with pytest.raises(OCRDependencyError):
        ocr_image("dummy_path.png")
