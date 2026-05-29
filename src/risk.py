# src/risk.py

def compute_risk(entities):
    """
    Computes a risk level (HIGH, MEDIUM, LOW) based on the categories of extracted entities.
    
    - HIGH: contains MEDICAL_CONDITION, MEDICATION, or HEALTH_INSURANCE_ID.
    - MEDIUM: contains EMAIL, PHONE, ADDRESS, or DATE_OF_BIRTH (but no HIGH categories).
    - LOW: no entities extracted or only entities that do not fall under the above.
    """
    if not entities:
        return "LOW"
        
    high_risk_types = {'MEDICAL_CONDITION', 'MEDICATION', 'HEALTH_INSURANCE_ID'}
    medium_risk_types = {'EMAIL', 'PHONE', 'ADDRESS', 'DATE_OF_BIRTH'}
    
    entity_types = {e['type'].upper() for e in entities}
    
    if entity_types & high_risk_types:
        return "HIGH"
    elif entity_types & medium_risk_types:
        return "MEDIUM"
        
    return "LOW"
