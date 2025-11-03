from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from ....domain.documents.schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from ....domain.documents import services

documents_router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@documents_router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    file: Optional[UploadFile] = File(None),
    file_name: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    project_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    artifact_type: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    size: Optional[int] = Form(None),
):
    """
    Create a new document with file upload (multipart/form-data).
    """
    print(f"[DEBUG : documents.py] Creating document - file: {file}, project_id: {project_id}")
    
    # Use filename from UploadFile if file_name not provided
    if not file_name and file:
        file_name = file.filename or "uploaded_file"
    elif not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_name is required"
        )
    
    # Use file_name as title if title not provided
    if not title:
        title = file_name
    
    # Get file size from file if not provided
    if not size and file and file.size:
        size = file.size
    
    # Parse tags if provided as string
    tags_list = []
    if tags:
        try:
            import json
            tags_list = json.loads(tags)
        except:
            # If not JSON, treat as comma-separated
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # Parse metadata if provided
    metadata_dict = {}
    if metadata:
        try:
            import json
            metadata_dict = json.loads(metadata)
        except:
            metadata_dict = {}
    
    # Create DocumentCreate payload
    doc_data = DocumentCreate(
        file_name=file_name,
        title=title,
        project_id=project_id,
        user_id=user_id or "",
        type=type,
        artifact_type=artifact_type,
        tags=tags_list,
        metadata=metadata_dict,
        size=size,
    )
    
    # TODO: Handle file storage/processing here
    # For now, just create the document metadata
    return await services.create(doc_data)

@documents_router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    print(f"[DEBUG : documents.py] Listing all documents")
    return await services.list_all()

@documents_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    print(f"[DEBUG : documents.py] Getting document: {document_id}")
    return await services.get(document_id)

@documents_router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, payload: DocumentUpdate):
    print(f"[DEBUG : documents.py] Updating document: {document_id}")
    return await services.update(document_id, payload)

@documents_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    print(f"[DEBUG : documents.py] Deleting document: {document_id}")
    return await services.delete(document_id)