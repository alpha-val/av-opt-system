import fitz  # PyMuPDF
import pandas as pd
from app_v2.core.database import get_database
from app_v2.repositories.project_repo import ProjectRepository
from app_v2.repositories.scenario_repo import ScenarioRepository
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
    tables = pd.read_pdf(pdf_path, pages='all')  # Using tabula-py or camelot-py
    return tables

async def transform_data(text, tables):
    """Transform extracted text and tables into structured data."""
    # Example transformation logic
    project_data = {
        "name": "Extracted Project Name",
        "description": "Extracted Project Description",
        # Additional fields...
    }
    
    scenarios = []
    for table in tables:
        for index, row in table.iterrows():
            scenario = {
                "name": row['Scenario Name'],
                "description": row['Description'],
                # Additional fields...
            }
            scenarios.append(scenario)

    return project_data, scenarios

async def load_data_to_db(project_data, scenarios):
    """Load data into the database."""
    db = await get_database()
    
    project_repo = ProjectRepository(db)
    scenario_repo = ScenarioRepository(db)

    project_id = await project_repo.create(project_data)
    
    for scenario in scenarios:
        scenario['project_id'] = project_id
        await scenario_repo.create(scenario)

async def etl_pipeline(pdf_path):
    """Main ETL pipeline function."""
    text = await extract_text_from_pdf(pdf_path)
    tables = await extract_tables_from_pdf(pdf_path)
    project_data, scenarios = await transform_data(text, tables)
    await load_data_to_db(project_data, scenarios)

# Example usage
# asyncio.run(etl_pipeline("path/to/project_report.pdf"))