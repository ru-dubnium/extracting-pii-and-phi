# src/merger.py

def merge_entities(regex_list, llm_list):
    """
    Combines regex-extracted and LLM-extracted entities, resolving duplicates and overlaps.
    
    1. If the same entity (by type and case-insensitive value) is present in both lists, 
       keep the regex version (regex is preferred).
    2. If two entities have overlapping character spans, resolve the conflict:
       - Keep the entity with the longer span (most specific match).
       - If span lengths are identical, keep the one with higher confidence.
       - If confidence is also identical, keep the regex entity.
    """
    # 1. Deduplicate by type and value: key is (type, lowercase_value)
    unique_entities = {}
    
    # Process regex entities first (so they are the default)
    for e in regex_list:
        key = (e['type'], e['value'].lower())
        unique_entities[key] = e
        
    # Process LLM entities. Only add if not already present.
    for e in llm_list:
        key = (e['type'], e['value'].lower())
        if key not in unique_entities:
            unique_entities[key] = e
            
    entities = list(unique_entities.values())
    
    # Separate entities with valid start/end offsets from those without
    positioned = [e for e in entities if e['start'] != -1 and e['end'] != -1]
    unpositioned = [e for e in entities if e['start'] == -1 or e['end'] == -1]
    
    TYPE_PRIORITY = {
        "EMAIL": 1,
        "DATE_OF_BIRTH": 1,
        "HEALTH_INSURANCE_ID": 1,
        "MEDICAL_CONDITION": 2,
        "MEDICATION": 2,
        "ADDRESS": 2,
        "PHONE": 3
    }
    
    # 2. Resolve overlaps for positioned entities
    # Sort by start index ascending, then longest match (end index descending),
    # then more specific type first (type priority), then higher confidence, then regex first.
    positioned.sort(key=lambda x: (
        x['start'], 
        -x['end'], 
        TYPE_PRIORITY.get(x['type'], 9),
        -x['confidence'], 
        0 if x['source'] == 'regex' else 1
    ))
    
    resolved = []
    for current in positioned:
        if not resolved:
            resolved.append(current)
            continue
            
        prev = resolved[-1]
        
        # Overlap check: Since they are sorted by start index, they overlap if:
        # current.start < prev.end
        if current['start'] < prev['end']:
            prev_len = prev['end'] - prev['start']
            current_len = current['end'] - current['start']
            
            if current_len > prev_len:
                # Current entity is longer; replace the previous one
                resolved[-1] = current
            elif current_len == prev_len:
                # Equal length, compare confidence
                if current['confidence'] > prev['confidence']:
                    resolved[-1] = current
                elif current['confidence'] == prev['confidence']:
                    # Prefer regex source
                    if current['source'] == 'regex' and prev['source'] != 'regex':
                        resolved[-1] = current
            else:
                # Previous entity is longer; discard current entity
                pass
        else:
            # No overlap, safely append
            resolved.append(current)
            
    # Combine back positioned and unpositioned entities
    return resolved + unpositioned
