### Step 1: Extract Data from PDF Files

1. **PDF Parsing**:
   - Use libraries like `PyMuPDF`, `pdfplumber`, or `PyPDF2` to extract text from PDF files.
   - For tabular data, consider using `tabula-py` or `camelot-py` to extract tables directly.

   ```python
   import pdfplumber

   def extract_text_from_pdf(pdf_path):
       with pdfplumber.open(pdf_path) as pdf:
           text = ""
           for page in pdf.pages:
               text += page.extract_text() + "\n"
       return text

   def extract_tables_from_pdf(pdf_path):
       tables = []
       with pdfplumber.open(pdf_path) as pdf:
           for page in pdf.pages:
               tables.extend(page.extract_tables())
       return tables
   ```

2. **File Handling**:
   - Implement a file upload mechanism to handle incoming PDF files, possibly using FastAPI's file upload capabilities.

### Step 2: Transform Data

1. **Data Cleaning**:
   - Clean the extracted text to remove unnecessary whitespace, headers, footers, and any irrelevant information.
   - Use regular expressions or string manipulation to format the data correctly.

   ```python
   import re

   def clean_extracted_text(text):
       # Remove unwanted characters and whitespace
       cleaned_text = re.sub(r'\s+', ' ', text).strip()
       return cleaned_text
   ```

2. **Data Structuring**:
   - Parse the cleaned text to extract relevant information such as project details, equipment specifications, and cost estimates.
   - Create structured data models that align with the existing schemas in `app_v2`.

   ```python
   def parse_project_report(text):
       # Example parsing logic
       project_data = {
           "name": extract_name(text),
           "description": extract_description(text),
           # Add more fields as necessary
       }
       return project_data
   ```

3. **Tabular Data Transformation**:
   - Convert extracted tables into structured data formats (e.g., dictionaries or data classes) that match the database schema.

   ```python
   def transform_table_data(tables):
       equipment_data = []
       for table in tables:
           for row in table[1:]:  # Skip header
               equipment_data.append({
                   "manufacturer": row[0],
                   "model": row[1],
                   "capacity_tph": float(row[2]),
                   "purchase_cost": float(row[3]),
                   # Map other fields as necessary
               })
       return equipment_data
   ```

### Step 3: Load Data into the Database

1. **Database Connection**:
   - Use the existing database connection functionality from `app_v2` to connect to the MongoDB database.

   ```python
   from app_v2.core.database import get_database

   async def get_db():
       db = await get_database()
       return db
   ```

2. **Insert Data**:
   - Use the appropriate repository methods to insert the structured data into the database. This may involve creating new project, scenario, option, and cost estimate records.

   ```python
   from app_v2.repositories.project_repo import ProjectRepository
   from app_v2.repositories.option_repo import OptionRepository

   async def load_data_to_db(project_data, equipment_data):
       db = await get_db()
       project_repo = ProjectRepository(db)
       option_repo = OptionRepository(db)

       # Insert project data
       project_id = await project_repo.create(project_data)

       # Insert equipment data
       for equipment in equipment_data:
           equipment["project_id"] = project_id
           await option_repo.create(equipment)
   ```

### Step 4: Orchestrate the ETL Process

1. **ETL Function**:
   - Create a function that orchestrates the entire ETL process, calling the extract, transform, and load functions in sequence.

   ```python
   async def etl_pipeline(pdf_path):
       # Extract
       text = extract_text_from_pdf(pdf_path)
       tables = extract_tables_from_pdf(pdf_path)

       # Transform
       cleaned_text = clean_extracted_text(text)
       project_data = parse_project_report(cleaned_text)
       equipment_data = transform_table_data(tables)

       # Load
       await load_data_to_db(project_data, equipment_data)
   ```

2. **Triggering the ETL Process**:
   - Implement an API endpoint in FastAPI to trigger the ETL process when a new PDF file is uploaded.

   ```python
   from fastapi import APIRouter, UploadFile, File

   router = APIRouter()

   @router.post("/upload-pdf")
   async def upload_pdf(file: UploadFile = File(...)):
       pdf_path = f"/path/to/save/{file.filename}"
       with open(pdf_path, "wb") as f:
           f.write(await file.read())
       await etl_pipeline(pdf_path)
       return {"message": "ETL process completed successfully."}
   ```

### Conclusion

This ETL pipeline provides a structured approach to ingesting data from PDF files into the `app_v2` backend. It extracts unstructured text and tabular data, transforms it into structured formats, and loads it into the database, facilitating the creation of scenarios, options, and cost estimates. Adjustments may be necessary based on the specific structure of the PDF files and the requirements of the application.