import fitz  # PyMuPDF
import pandas as pd
import os

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_tables_from_pdf(pdf_path):
    tables = []
    # Use pdfplumber or similar to extract tables
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    return tables