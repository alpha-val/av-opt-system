from fastapi import APIRouter, HTTPException, status
from typing import List
from ....domain.projects.schemas import ProjectCreate, ProjectUpdate, ProjectOut
from ....domain.projects.schemas import ProjectEntitiesRelationsOut
from ....domain.projects import services

projects_router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@projects_router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate):
    print(f"[DEBUG : projects.py] Received payload for project creation: {payload}")
    return await services.create(payload)


@projects_router.get("/", response_model=List[ProjectOut])
async def list_projects():
    return await services.list_all()


@projects_router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str):
    proj = await services.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@projects_router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, payload: ProjectUpdate):
    proj = await services.update(project_id, payload)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@projects_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    ok = await services.delete(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

# Clear project data: delete all documents, chunks, entities, relations, tables, scenarios, cost estimates
@projects_router.delete("/{project_id}/data", status_code=status.HTTP_200_OK)
async def clear_project_data(project_id: str):
    result = await services.clear_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result

# Fetch project entities and relations
@projects_router.get("/{project_id}/entities_relations", response_model=ProjectEntitiesRelationsOut)
async def get_project_entities_relations(project_id: str):
    result = await services.get_entities_relations(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result