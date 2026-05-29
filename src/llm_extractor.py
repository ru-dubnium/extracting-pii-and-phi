# src/llm_extractor.py
import json
import re
import logging

logger = logging.getLogger(__name__)

# Local Heuristics Fallback Lists
HEURISTIC_CONDITIONS = {
    "diabetes", "hypertension", "asthma", "cancer", "depression", "anxiety",
    "arthritis", "heart disease", "alzheimer's", "dementia", "stroke", 
    "hiv", "aids", "influenza", "covid-19", "copd", "migraine", "epilepsy",
    "hepatitis", "tuberculosis", "osteoporosis", "allergies"
}

HEURISTIC_MEDICATIONS = {
    "insulin", "metformin", "lisinopril", "albuterol", "atorvastatin", 
    "ibuprofen", "aspirin", "levothyroxine", "amoxicillin", "gabapentin",
    "sertraline", "omeprazole", "losartan", "metoprolol", "prednisone",
    "lipitor", "synthroid", "vicodin", "amodip", "xanax"
}

# Matches typical US and international address structures (including P.O. Box formats)
HEURISTIC_ADDRESS_PATTERN = (
    r'\b(?:P\.O\.\s+Box\s+\d+|'
    r'\d{1,5}\s+[A-Za-z0-9\s.#-]{1,25}\s+'
    r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Pl|Place|Circle|Cir))\b'
    r'(?:\s*[,#-]\s*(?:Apt|Suite|Unit|Floor|Building|Bldg|#|\d+)\s*[A-Za-z0-9]*)?'
    r'(?:\s*,\s*[A-Za-z\s]{2,20})?'
    r'(?:\s*,\s*[A-Z]{2})?'
    r'(?:\s*\d{5})?'
)

def heuristic_extract(text):
    """
    Fallback extractor using regex and keyword lists when Ollama is unavailable.
    """
    entities = []
    text_lower = text.lower()
    
    # 1. Extract addresses using pattern
    for match in re.finditer(HEURISTIC_ADDRESS_PATTERN, text, re.IGNORECASE):
        val = match.group().strip()
        # Avoid matching extremely short sub-spans or single numbers
        if len(val) > 8:
            entities.append({
                "type": "ADDRESS",
                "value": val,
                "confidence": 0.8,
                "start": match.start(),
                "end": match.end(),
                "source": "heuristic_fallback"
            })
            
    # 2. Extract medical conditions by keyword matching (supporting multi-word phrases)
    for condition in HEURISTIC_CONDITIONS:
        for match in re.finditer(rf'\b{re.escape(condition)}\b', text, re.IGNORECASE):
            entities.append({
                "type": "MEDICAL_CONDITION",
                "value": match.group(),
                "confidence": 0.8,
                "start": match.start(),
                "end": match.end(),
                "source": "heuristic_fallback"
            })
                
    # 3. Extract medications by keyword matching
    for medication in HEURISTIC_MEDICATIONS:
        for match in re.finditer(rf'\b{re.escape(medication)}\b', text, re.IGNORECASE):
            entities.append({
                "type": "MEDICATION",
                "value": match.group(),
                "confidence": 0.8,
                "start": match.start(),
                "end": match.end(),
                "source": "heuristic_fallback"
            })
                
    return entities

def llm_extract(text, model='llama3.2'):
    """
    Queries local Ollama LLM to extract MEDICAL_CONDITION, MEDICATION, and ADDRESS.
    Falls back to heuristic_extract if Ollama is not running or fails.
    """
    if not text:
        return []

    prompt = f"""You are a PII/PHI extraction assistant. Extract from the text only:
- MEDICAL_CONDITION (e.g., diabetes, hypertension, asthma)
- MEDICATION (e.g., Metformin, Lisinopril, insulin)
- ADDRESS (full address, any format)

Return a valid JSON array: [{{"type": "MEDICAL_CONDITION|MEDICATION|ADDRESS", "value": "exact_extracted_text", "confidence": 0.9}}]
Only include keys 'type', 'value', and 'confidence'.
If none are found, return [].

Text: {text}
"""
    try:
        import ollama
        # Try listing to check if the Ollama daemon is running
        ollama.list()
        
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            format='json',
            options={'temperature': 0.1}
        )
        content = response['message']['content']
        data = json.loads(content)
        
        extracted = []
        for item in data:
            if not isinstance(item, dict) or 'type' not in item or 'value' not in item:
                continue
            
            # Ensure the extracted type is valid
            etype = item['type'].upper()
            if etype not in {'MEDICAL_CONDITION', 'MEDICATION', 'ADDRESS'}:
                continue
                
            val = item['value']
            # Only add if the value exists in the source text (avoid hallucination)
            if val.lower() in text.lower():
                extracted.append({
                    "type": etype,
                    "value": val,
                    "confidence": float(item.get('confidence', 0.9)),
                    "start": -1,  # Post-processor / HybridExtractor will compute indices
                    "end": -1,
                    "source": "llm"
                })
        return extracted

    except Exception as e:
        logger.warning(f"Ollama extraction failed or service unavailable ({e}). Falling back to heuristics...")
        return heuristic_extract(text)
