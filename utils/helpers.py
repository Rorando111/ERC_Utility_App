import re

def sanitize_filename(filename: str) -> str:
    """
    Removes or replaces invalid characters from a filename.
    """
    # Remove special characters that are invalid in filenames
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    return sanitized.strip().replace(" ", "_")
