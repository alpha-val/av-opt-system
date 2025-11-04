"""
Table extraction from PDF files.

Extracts both lattice and stream type tables from PDFs.
"""

from typing import List, Dict, Any, Optional
from .pdf_table_extractor import extract_pdf_tables
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TableExtractor:
    """Extract tables from PDF files."""
    
    def extract_tables(
        self,
        pdf_bytes: bytes,
        pages: Optional[str] = None,
        dpi: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF.
        
        Args:
            pdf_bytes: PDF file content as bytes
            pages: Optional page range filter (e.g., "1-5,10")
            dpi: DPI for table extraction (default: 300)
            
        Returns:
            List of table dictionaries with:
            - table_id: Unique table identifier
            - page: Page number where table was found
            - data: Table data (list of rows, each row is list of cells)
            - headers: Table headers (if detected)
            - table_type: "lattice" or "stream"
            - metadata: Additional table metadata
        """
        logger.info("Extracting tables from PDF")
        
        try:
            # Use existing table extraction functionality
            # Returns: [{ "df": pandas.DataFrame, "meta": {...}}]
            table_results = extract_pdf_tables(
                pdf_bytes,
                pages=pages,
                dpi=dpi
            )
            
            # Normalize table results
            tables = []
            for idx, table_result in enumerate(table_results):
                df = table_result.get("df")
                meta = table_result.get("meta", {})
                
                # Extract page number
                page = meta.get("page", 0)
                table_id = f"table_{page}_{idx}"
                
                # Convert DataFrame to list of rows
                data = []
                headers = []
                if df is not None and isinstance(df, pd.DataFrame):
                    # Convert DataFrame to list of lists
                    data = df.values.tolist()
                    headers = df.columns.tolist()
                elif df is not None:
                    # If df is not a DataFrame, try to convert it
                    try:
                        if hasattr(df, 'tolist'):
                            data = df.tolist()
                        elif isinstance(df, list):
                            data = df
                    except Exception as e:
                        logger.warning(f"Could not convert table data to list: {e}")
                
                # Determine table type from meta
                table_type = "lattice" if meta.get("flavor") == "lattice" else "stream" if meta.get("flavor") == "stream" else "ocr" if meta.get("flavor") == "ocr" else "unknown"
                
                table = {
                    "table_id": table_id,
                    "id": table_id,
                    "page": page,
                    "data": data,
                    "headers": headers,
                    "table_type": table_type,
                    "metadata": {
                        "extraction_method": meta.get("flavor", "unknown"),
                        "dpi": dpi,
                        "bbox": meta.get("bbox"),
                        "index": meta.get("index", idx),
                        **{k: v for k, v in meta.items() if k not in ["page", "flavor", "bbox", "index"]},
                    },
                }
                
                tables.append(table)
            
            logger.info(f"Extracted {len(tables)} tables from PDF")
            
            return tables
            
        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            raise
    
    def format_table_for_llm(self, table: Dict[str, Any]) -> str:
        """
        Format table data as text for LLM processing.
        
        Args:
            table: Table dictionary
            
        Returns:
            Formatted table text string
        """
        table_id = table.get("table_id", "unknown")
        page = table.get("page", 0)
        headers = table.get("headers", [])
        data = table.get("data", [])
        table_type = table.get("table_type", "unknown")
        
        # Build formatted table
        lines = []
        lines.append(f"[TABLE table_id=\"{table_id}\" table_type=\"{table_type}\" page=\"{page}\"]")
        
        # Add headers if available
        if headers:
            header_line = " | ".join(str(h) if h else "" for h in headers)
            lines.append(f"| {header_line} |")
        
        # Add rows
        for row in data:
            row_line = " | ".join(str(cell) if cell else "" for cell in row)
            lines.append(f"| {row_line} |")
        
        lines.append("[/TABLE]")
        
        return "\n".join(lines)
    
    def create_table_chunks(
        self,
        tables: List[Dict[str, Any]],
        doc_id: str,
        max_rows_per_chunk: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from tables for LLM processing.
        
        Args:
            tables: List of table dictionaries
            doc_id: Document identifier
            max_rows_per_chunk: Maximum rows per chunk (default: 50)
            
        Returns:
            List of chunk dictionaries containing table data
        """
        chunks = []
        chunk_seq = 1
        
        for table in tables:
            table_id = table.get("table_id")
            data = table.get("data", [])
            headers = table.get("headers", [])
            
            # Split table into chunks if it's too large
            if len(data) <= max_rows_per_chunk:
                # Single chunk for this table
                formatted_table = self.format_table_for_llm(table)
                
                chunk = {
                    "id": f"{doc_id}_table_{table_id}_chunk_1",
                    "chunk_id": f"{doc_id}_table_{table_id}_chunk_1",
                    "doc_id": doc_id,
                    "seq": chunk_seq,
                    "text": formatted_table,
                    "table_id": table_id,
                    "page": table.get("page"),
                    "chunk_type": "table",
                    "properties": {
                        "table_type": table.get("table_type"),
                        "row_count": len(data),
                        "column_count": len(headers) if headers else len(data[0]) if data else 0,
                    },
                }
                
                chunks.append(chunk)
                chunk_seq += 1
            else:
                # Split into multiple chunks
                for i in range(0, len(data), max_rows_per_chunk):
                    chunk_data = data[i : i + max_rows_per_chunk]
                    
                    # Create sub-table for this chunk
                    sub_table = {
                        **table,
                        "data": chunk_data,
                        "chunk_index": i // max_rows_per_chunk,
                    }
                    
                    formatted_table = self.format_table_for_llm(sub_table)
                    
                    chunk = {
                        "id": f"{doc_id}_table_{table_id}_chunk_{i // max_rows_per_chunk + 1}",
                        "chunk_id": f"{doc_id}_table_{table_id}_chunk_{i // max_rows_per_chunk + 1}",
                        "doc_id": doc_id,
                        "seq": chunk_seq,
                        "text": formatted_table,
                        "table_id": table_id,
                        "page": table.get("page"),
                        "chunk_type": "table",
                        "properties": {
                            "table_type": table.get("table_type"),
                            "row_start": i,
                            "row_end": i + len(chunk_data),
                            "row_count": len(chunk_data),
                            "column_count": len(headers) if headers else len(chunk_data[0]) if chunk_data else 0,
                        },
                    }
                    
                    chunks.append(chunk)
                    chunk_seq += 1
        
        logger.info(f"Created {len(chunks)} table chunks from {len(tables)} tables")
        
        return chunks

