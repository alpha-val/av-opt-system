"""
File storage service using MongoDB GridFS.

Handles storage and retrieval of project files (PDF, Excel, CSV).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from gridfs import GridFS
from gridfs.errors import NoFile
from ...adapters.mongo.client import db
import hashlib
import logging

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for storing and retrieving files using MongoDB GridFS."""
    
    def __init__(self):
        """Initialize GridFS instance."""
        self._db = db()
        self._fs = GridFS(self._db, collection="project_files")
    
    def store_file(
        self,
        file_bytes: bytes,
        filename: str,
        project_id: str,
        artifact_type: str,
        content_type: str,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Store a file in GridFS.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            project_id: Project identifier
            artifact_type: Type of artifact ("base_case" or "tabular_data")
            content_type: MIME type of the file
            user_id: Optional user identifier
            
        Returns:
            Document ID (GridFS file_id as string)
        """
        # Calculate SHA256 hash for deduplication/verification
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Store file in GridFS with metadata
        file_id = self._fs.put(
            file_bytes,
            filename=filename,
            project_id=project_id,
            artifact_type=artifact_type,
            content_type=content_type,
            user_id=user_id or "",
            sha256=file_hash,
            upload_date=None,  # GridFS will set this automatically
        )
        
        doc_id = str(file_id)
        logger.info(
            f"Stored file in GridFS: {filename} -> {doc_id} "
            f"(project: {project_id}, type: {artifact_type}, size: {len(file_bytes)} bytes)"
        )
        
        return doc_id
    
    def get_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve a file from GridFS by ID.
        
        Args:
            file_id: GridFS file ID (as string)
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            # Convert string ID to ObjectId if needed
            from bson import ObjectId
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
            
            file_data = self._fs.get(file_id)
            return file_data.read()
        except NoFile:
            logger.warning(f"File not found in GridFS: {file_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {e}", exc_info=True)
            return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata without reading the file content.
        
        Args:
            file_id: GridFS file ID (as string)
            
        Returns:
            File metadata dictionary, or None if not found
        """
        try:
            from bson import ObjectId
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
            
            file_data = self._fs.get(file_id)
            return {
                "file_id": str(file_data._id),
                "filename": file_data.filename,
                "length": file_data.length,
                "upload_date": file_data.upload_date,
                "content_type": file_data.content_type,
                "project_id": file_data.project_id,
                "artifact_type": file_data.artifact_type,
                "sha256": getattr(file_data, "sha256", None),
            }
        except NoFile:
            logger.warning(f"File metadata not found: {file_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving file metadata {file_id}: {e}", exc_info=True)
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from GridFS.
        
        Args:
            file_id: GridFS file ID (as string)
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            from bson import ObjectId
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
            
            self._fs.delete(file_id)
            logger.info(f"Deleted file from GridFS: {file_id}")
            return True
        except NoFile:
            logger.warning(f"File not found for deletion: {file_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}", exc_info=True)
            return False
    
    def list_project_files(self, project_id: str, artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all files for a project.
        
        Args:
            project_id: Project identifier
            artifact_type: Optional filter by artifact type
            
        Returns:
            List of file metadata dictionaries
        """
        query = {"project_id": project_id}
        if artifact_type:
            query["artifact_type"] = artifact_type
        
        files = []
        for grid_file in self._fs.find(query):
            files.append({
                "file_id": str(grid_file._id),
                "filename": grid_file.filename,
                "length": grid_file.length,
                "upload_date": grid_file.upload_date,
                "content_type": grid_file.content_type,
                "artifact_type": grid_file.artifact_type,
                "sha256": getattr(grid_file, "sha256", None),
            })
        
        return files

