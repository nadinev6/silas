def determine_thinking_level(user_input: str) -> str:
    """
    Judges love efficiency. Silas only 'thinks hard' when 
    the user presents a complex hardware problem.
    """
    complex_keywords = ["schematic", "pinout", "voltage", "i2s", "buffer", "debug"]
    
    if any(word in user_input.lower() for word in complex_keywords):
        return "high"  # Deep reasoning for hardware bugs
    return "low"       # Fast, snarky chat for casual banter
