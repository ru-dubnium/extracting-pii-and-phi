# tests/test_golden.py
import os
import json
import pytest
from src.extractor import HybridExtractor

# Resolve the path to the golden dataset JSON file
GOLDEN_DATASET_PATH = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')

def load_golden_dataset():
    with open(GOLDEN_DATASET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

golden_dataset = load_golden_dataset()

@pytest.mark.parametrize("test_case", golden_dataset)
def test_golden_prompts(test_case):
    """
    Test the hybrid extractor against the golden dataset prompts.
    Ensures that all expected entities are successfully detected.
    """
    extractor = HybridExtractor()
    extracted_entities = extractor.extract(test_case["prompt"])
    expected_entities = test_case["expected"]
    
    # We want to check if all expected entities are present in extracted_entities.
    # To handle minor formatting/spacing/punctuation discrepancies (especially in addresses/medications),
    # we verify that for each expected entity, there exists an extracted entity of the same type
    # where the expected value is a substring of the extracted value, or vice-versa.
    missing_entities = []
    
    for expected in expected_entities:
        exp_type = expected["type"]
        exp_val = expected["value"].lower().strip()
        
        match_found = False
        for ext in extracted_entities:
            ext_type = ext["type"]
            ext_val = ext["value"].lower().strip()
            
            if exp_type == ext_type:
                # Check for exact match or substring containment
                if exp_val in ext_val or ext_val in exp_val:
                    match_found = True
                    break
        
        if not match_found:
            missing_entities.append(expected)
            
    assert not missing_entities, (
        f"Test case #{test_case['id']} failed!\n"
        f"Prompt: '{test_case['prompt']}'\n"
        f"Missing Expected Entities: {missing_entities}\n"
        f"Extracted Entities: {extracted_entities}"
    )
