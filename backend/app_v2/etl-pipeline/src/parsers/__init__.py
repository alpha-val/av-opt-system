   import pdfplumber

   def extract_text_from_pdf(pdf_path):
       with pdfplumber.open(pdf_path) as pdf:
           text = ""
           for page in pdf.pages:
               text += page.extract_text() + "\n"
       return text

   def extract_tables_from_pdf(pdf_path):
       tables = []
       tables = camelot.read_pdf(pdf_path, pages='all')
       return [table.df for table in tables]