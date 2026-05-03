import PyPDF2

def extract_text_from_cv(file_path: str) -> str:
    if not file_path.endswith(".pdf"):
        raise ValueError("Only PDF files are supported in this version.")

    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text
