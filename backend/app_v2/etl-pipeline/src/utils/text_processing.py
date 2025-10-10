import fitz  # PyMuPDF
import pandas as pd
from app_v2.core.database import get_database
from app_v2.repositories.project_repo import ProjectRepository
from app_v2.repositories.option_repo import OptionRepository
from app_v2.repositories.equipment_repo import EquipmentRepository

async def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

async def extract_tables_from_pdf(pdf_path):
    """Extract tables from a PDF file."""
    # Example using tabula-py
    tables = pd.read_csv(pdf_path)  # Replace with actual table extraction logic
    return tables

async def transform_data(text, tables):
    """Transform extracted text and tables into structured data."""
    # Example transformation logic
    project_data = {
        "name": "Extracted Project Name",
        "description": "Extracted Project Description",
        # Add more fields as necessary
    }
    
    equipment_data = []
    for index, row in tables.iterrows():
        equipment_data.append({
            "manufacturer": row['Manufacturer'],
            "model": row['Model'],
            "purchase_cost": row['Purchase Cost'],
            # Map other fields as necessary
        })
    
    return project_data, equipment_data

async def load_data_to_db(project_data, equipment_data):
    """Load transformed data into the database."""
    db = await get_database()
    project_repo = ProjectRepository(db)
    option_repo = OptionRepository(db)
    equipment_repo = EquipmentRepository(db)

    # Insert project data
    project_id = await project_repo.create(project_data)

    # Insert equipment data
    for equipment in equipment_data:
        equipment['project_id'] = project_id  # Link to project
        await equipment_repo.create(equipment)

async def etl_pipeline(pdf_path):
    """Main ETL pipeline function."""
    text = await extract_text_from_pdf(pdf_path)
    tables = await extract_tables_from_pdf(pdf_path)
    project_data, equipment_data = await transform_data(text, tables)
    await load_data_to_db(project_data, equipment_data)

# Example usage
# await etl_pipeline("path/to/project_report.pdf")