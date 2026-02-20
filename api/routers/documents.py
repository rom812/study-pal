"""API router for document operations."""

import asyncio
import logging
import shutil
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.dependencies import PROJECT_ROOT, get_or_create_chatbot

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    user_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
):
    """Upload a PDF file for ingestion."""
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Get chatbot (load lazy dependencies)
        chatbot = get_or_create_chatbot(user_id)

        # Save uploaded file temporarily
        upload_dir = PROJECT_ROOT / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"{user_id}_{file.filename}"

        try:
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Ingest the file (run in thread to avoid blocking loop)
            # ingest_material on LangGraphChatbot handles the RAG pipeline ingestion
            result = await asyncio.to_thread(chatbot.ingest_material, temp_path)
            # get_materials_count returns int
            chunks = await asyncio.to_thread(chatbot.get_materials_count)

            return {"message": result, "chunks": chunks, "filename": file.filename}

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
