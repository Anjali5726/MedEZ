from pypdf import PdfReader

def extract_text_from_pdf(file_path):
    """
    Reads a PDF file using pypdf and returns all text as a string.
    pypdf is a pure-Python library, which prevents DLL load errors on Windows.
    """
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Check if we actually got text
        if not text.strip():
            return None  # PDF might be a scanned image
            
        return text
        
    except Exception as e:
        return None