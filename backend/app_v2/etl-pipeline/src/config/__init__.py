import fitz  # PyMuPDF
import pandas as pd
from app_v2.core.database import get_database
from app_v2.repositories.project_repo import ProjectRepository
from app_v2.repositories.scenario_repo import ScenarioRepository
from app_v2.repositories.option_repo import OptionRepository
from app_v2.schemas.project import ProjectCreate
from app_v2.schemas.scenario import ScenarioCreate
from app_v2.schemas.option import OptionCreate

async def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

async def extract_tables_from_pdf(pdf_path):
    """Extract tables from a PDF file."""
    # Use tabula or camelot to extract tables
    tables = pd.read_csv(pdf_path)  # Placeholder for actual table extraction
    return tables

async def transform_data(text, tables):
    """Transform extracted text and tables into structured data."""
    # Example transformation logic
    project_data = {
        "name": "Extracted Project Name",
        "description": "Extracted Project Description",
        "metadata": {
            "country": "Chile",
            "region": "Antofagasta",
            # Additional metadata extraction logic
        }
    }
    
    # Transform tables into options or equipment specifications
    equipment_data = []
    for index, row in tables.iterrows():
        equipment_data.append({
            "name": row['model'],
            "purchase_cost": row['purchase_cost'],
            # Map other fields as necessary
        })
    
    return project_data, equipment_data

async def load_data_to_db(project_data, equipment_data):
    """Load transformed data into the database."""
    db = await get_database()
    
    project_repo = ProjectRepository(db)
    scenario_repo = ScenarioRepository(db)
    option_repo = OptionRepository(db)
    
    # Insert project
    project_create = ProjectCreate(**project_data)
    project = await project_repo.create(project_create)
    
    # Insert scenarios and options based on the project
    for equipment in equipment_data:
        option_create = OptionCreate(**equipment)
        await option_repo.create(option_create)

async def etl_pipeline(pdf_path):
    """Main ETL pipeline function."""
    text = await extract_text_from_pdf(pdf_path)
    tables = await extract_tables_from_pdf(pdf_path)
    project_data, equipment_data = await transform_data(text, tables)
    await load_data_to_db(project_data, equipment_data)

# Example usage
# asyncio.run(etl_pipeline("path/to/project_report.pdf"))