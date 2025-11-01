from fastapi import APIRouter, HTTPException, status
from typing import List
from ....domain.projects.schemas import ProjectCreate, ProjectUpdate, ProjectOut
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
