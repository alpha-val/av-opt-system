import fitz  # PyMuPDF
import pandas as pd
from tabula import read_pdf

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_tables_from_pdf(pdf_path):
    tables = read_pdf(pdf_path, pages='all', multiple_tables=True)
    return tables  # This will return a list of DataFrames