import pdfplumber

def extract_data_from_pdf(pdf_path):
    extracted_data = {
        "text": "",
        "tables": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_data["text"] += page.extract_text() + "\n"
            extracted_data["tables"].extend(page.extract_tables())
    
    return extracted_data