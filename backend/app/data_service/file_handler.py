import fitz  # PyMuPDF
from io import BytesIO
import asyncio

async def extract_text_from_pdf(file_obj) -> str:
    try:
        # Try to read if it's an async file (like FastAPI UploadFile)
        if hasattr(file_obj, "read") and asyncio.iscoroutinefunction(file_obj.read):
            pdf_bytes = await file_obj.read()
        elif hasattr(file_obj, "read"):  # synchronous file-like object
            pdf_bytes = file_obj.read()
        elif isinstance(file_obj, bytes):
            pdf_bytes = file_obj
        else:
            raise TypeError("Unsupported file type")

        pdf_stream = BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        extracted_text = ""
        for page in doc:
            text = page.get_text()
            # print(f"[DEBUG] Extracted text from page {page.number}: {text[:100]}...")  # Preview first 100 characters
            extracted_text += text if text else "\n[No extractable text]\n"
            print(f"[DEBUG] Page #{page.number} > TEXT LENGTH: {len(text)})")  # Preview first 100 characters
        print("[DEBUG] Extracted text > total length:", len(extracted_text))
        # print("[DEBUG] Extracted text preview:", extracted_text[:300])  # Preview first 300 characters
        return extracted_text

    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")