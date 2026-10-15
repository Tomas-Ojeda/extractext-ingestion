from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.api.dependencies import get_http_client
from app.services.document_ingestion import ingest_document


router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: str
    checksum: str


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    response: Response = None,
    client=Depends(get_http_client),
):
    file_bytes = await file.read()
    try:
        document, created = await ingest_document(file_bytes, file.filename or "", client)
    except HTTPException:
        raise

    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return DocumentResponse(
        id=document["id"],
        filename=document["filename"],
        content=document["content"],
        checksum=document["checksum"],
    )