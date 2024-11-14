from pathlib import Path

def get_prompt_by_number(prompt_number: int) -> str:
    """Get prompt text by its number from individual prompt files"""
    prompt_file = Path(f'prompts/{prompt_number:02d}_*.md')
    
    # Find matching file
    matches = list(Path('.').glob(str(prompt_file)))
    if not matches:
        raise ValueError(f"Invalid prompt number: {prompt_number}")
        
    # Read prompt content
    prompt_text = matches[0].read_text()
    
    return prompt_text.strip() 