# Document services
from typing import List, Optional
from .schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from . import repository as repo

async def create(data: DocumentCreate) -> DocumentResponse:
    return await repo.create_document(data)

async def list_all() -> List[DocumentResponse]:
    return await repo.list_all_documents()

async def get(document_id: str) -> Optional[DocumentResponse]:
    return await repo.get_document(document_id)

async def update(document_id: str, data: DocumentUpdate) -> Optional[DocumentResponse]:
    return await repo.update_document(document_id, data)

async def delete(document_id: str) -> bool:
    return await repo.delete_document(document_id)
