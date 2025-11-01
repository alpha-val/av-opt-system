from typing import List, Optional
from .schemas import ProjectCreate, ProjectUpdate, ProjectOut
from . import repository as repo

async def create(data: ProjectCreate) -> ProjectOut:
    return await repo.create_project(data)

async def list_all() -> List[ProjectOut]:
    return await repo.list_projects()

async def get(project_id: str) -> Optional[ProjectOut]:
    return await repo.get_project(project_id)

async def update(project_id: str, patch: ProjectUpdate) -> Optional[ProjectOut]:
    return await repo.update_project(project_id, patch)

async def delete(project_id: str) -> bool:
    return await repo.delete_project(project_id)
