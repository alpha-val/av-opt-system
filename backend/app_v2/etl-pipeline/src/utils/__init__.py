   import pdfplumber
   import pandas as pd

   def extract_text_from_pdf(pdf_path):
       with pdfplumber.open(pdf_path) as pdf:
           text = ""
           for page in pdf.pages:
               text += page.extract_text() + "\n"
       return text

   def extract_tables_from_pdf(pdf_path):
       tables = pd.read_csv(pdf_path)  # Example for CSV; use appropriate library for PDF tables
       return tables