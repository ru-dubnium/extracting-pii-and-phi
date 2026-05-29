# src/extractor.py
import re
from .regex_extractor import regex_extract
from .llm_extractor import llm_extract
from .merger import merge_entities
from .ocr import ocr_image

class HybridExtractor:
    """
    Main orchestrator for PII/PHI extraction. Supports text and image inputs.
    Combines regex-based and local LLM-based extraction, then resolves overlapping entities.
    """
    def __init__(self, default_model='llama3.2'):
        self.default_model = default_model

    def extract(self, source, is_image=False, model=None):
        """
        Extracts PII/PHI entities from a text prompt or an image.
        
        Args:
            source (str): The raw text prompt OR file path to the image.
            is_image (bool): If True, treats source as an image path and performs OCR first.
            model (str): The local LLM model name to use (defaults to self.default_model).
            
        Returns:
            list: List of extracted and merged entities.
        """
        if not source:
            return []
            
        if is_image:
            text = ocr_image(source)
        else:
            text = source
            
        model_name = model or self.default_model
        
        # 1. Run extractors
        regex_entities = regex_extract(text)
        llm_entities = llm_extract(text, model=model_name)
        
        # 2. For LLM entities, resolve start/end offsets dynamically in the raw text
        for e in llm_entities:
            if e['start'] == -1:
                val = e['value']
                # Search case-insensitively in the text
                try:
                    matches = list(re.finditer(re.escape(val), text, re.IGNORECASE))
                    if matches:
                        # Use the first match location
                        match = matches[0]
                        e['start'] = match.start()
                        e['end'] = match.end()
                        e['value'] = match.group()  # Use exact casing from raw text
                except Exception:
                    # Basic fallback
                    pos = text.lower().find(val.lower())
                    if pos != -1:
                        e['start'] = pos
                        e['end'] = pos + len(val)
                        e['value'] = text[pos:pos+len(val)]
                        
        # 3. Merge and deduplicate
        merged = merge_entities(regex_entities, llm_entities)
        return merged
