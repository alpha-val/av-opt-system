import os
import pdfplumber

def extract_data_from_pdf(pdf_path):
    text_data = ""
    table_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_data += page.extract_text() + "\n"
            tables = page.extract_tables()
            for table in tables:
                table_data.append(table)

    return text_data, table_data