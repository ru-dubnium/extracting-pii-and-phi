# src/regex_extractor.py
import re

PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "PHONE": r'(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{4}\b',
    # Matches: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, and textual dates like January 15, 1990
    "DATE_OF_BIRTH": (
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|'
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|'
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b|'
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
    ),
    # Matches: Broad health insurance format (2-3 letters followed by 6-10 digits) or SSN style 9-digit ID
    "HEALTH_INSURANCE_ID": r'\b[A-Z]{2,3}\d{6,10}\b|\b\d{3}-\d{2}-\d{4}\b',
}

def regex_extract(text):
    """
    Extracts PII entities based on regular expressions.
    Returns a list of dictionaries with type, value, confidence, start, end, and source.
    """
    if not text:
        return []
    
    entities = []
    for etype, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                "type": etype,
                "value": match.group(),
                "confidence": 1.0,  # Regex is high confidence
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })
    return entities
