import fitz  # PyMuPDF
import re
from app_v2.core.database import get_database
from app_v2.repositories.project_repo import ProjectRepository
from app_v2.repositories.equipment_repo import EquipmentRepository

async def extract_data_from_pdf(pdf_path):
    # Extract text from PDF
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def transform_data(raw_text):
    # Example transformation logic
    project_data = {}
    equipment_data = []

    # Extract project information using regex
    project_match = re.search(r'Project Name:\s*(.*)', raw_text)
    if project_match:
        project_data['name'] = project_match.group(1)

    # Extract equipment specifications
    equipment_matches = re.findall(r'Equipment:\s*(.*)', raw_text)
    for match in equipment_matches:
        equipment_data.append({'name': match})

    return project_data, equipment_data

async def load_data_to_db(project_data, equipment_data):
    db = await get_database()
    project_repo = ProjectRepository(db)
    equipment_repo = EquipmentRepository(db)

    # Insert project data
    project_id = await project_repo.create(project_data)

    # Insert equipment data
    for equipment in equipment_data:
        equipment['project_id'] = project_id
        await equipment_repo.create(equipment)

async def etl_pipeline(pdf_path):
    raw_text = await extract_data_from_pdf(pdf_path)
    project_data, equipment_data = transform_data(raw_text)
    await load_data_to_db(project_data, equipment_data)

# Example usage
# await etl_pipeline('/path/to/project_report.pdf')