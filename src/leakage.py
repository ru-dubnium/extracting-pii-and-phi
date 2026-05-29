# src/leakage.py

def detect_leakage(input_entities, output_entities):
    """
    Detects leakage by identifying which PII/PHI entities from the input prompt
    are present in the target LLM's output response.
    
    Args:
        input_entities (list): Entities extracted from the input prompt/source.
        output_entities (list): Entities extracted from the LLM's response.
        
    Returns:
        list: Entities that were present in the input and leaked into the output.
    """
    if not input_entities or not output_entities:
        return []
        
    # Build a set of lowercase values and types of input entities for case-insensitive matching
    input_keys = {(e['type'], e['value'].lower()) for e in input_entities}
    
    leaked = []
    seen = set()
    
    for e in output_entities:
        key = (e['type'], e['value'].lower())
        if key in input_keys:
            if key not in seen:
                seen.add(key)
                leaked.append(e)
                
    return leaked
