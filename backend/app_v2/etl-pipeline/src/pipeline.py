import pdfplumber

def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text_data = ""
        table_data = []
        
        for page in pdf.pages:
            text_data += page.extract_text() + "\n"
            tables = page.extract_tables()
            for table in tables:
                table_data.append(table)
                
    return text_data, table_data