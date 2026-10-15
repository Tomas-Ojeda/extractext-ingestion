import httpx
from fastapi import HTTPException, status

from config.settings import settings
from app.services.checksum_service import compute_checksum


DEFAULT_ERROR_MESSAGE = "Error inesperado al procesar el documento"


async def fetch_by_checksum(checksum: str, client: httpx.AsyncClient) -> dict | None:
    """Consulta storage por checksum. Devuelve None si no existe (404)."""
    url = f"{settings.storage_url}/api/v1/documents/by-checksum/{checksum}"
    try:
        response = await client.get(url, timeout=settings.storage_timeout_seconds)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al consultar documento por checksum: {str(exc)}",
        )

    if response.status_code == 200:
        return response.json()
    if response.status_code == 404:
        return None
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Error al consultar documento por checksum: {response.text}",
    )


def _extract_detail(response: httpx.Response, default: str) -> str:
    """Intenta obtener `detail` del JSON de una respuesta HTTP."""
    try:
        payload = response.json()
    except ValueError:
        return default
    if isinstance(payload, dict) and "detail" in payload:
        return str(payload["detail"])
    return default


async def extract_content(file_bytes: bytes, filename: str, client: httpx.AsyncClient) -> str:
    """Envía el PDF al extractor y devuelve el texto extraído."""
    url = f"{settings.extractor_url}/api/v1/extract"
    try:
        response = await client.post(
            url,
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=settings.extractor_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al extraer texto: {str(exc)}",
        )

    if 200 <= response.status_code < 300:
        try:
            return response.json().get("content", "")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Respuesta inválida del extractor",
            )
    if 400 <= response.status_code < 500:
        detail = _extract_detail(response, "Error de validación del PDF")
        raise HTTPException(status_code=response.status_code, detail=detail)
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Error al extraer texto: {response.text}",
    )


async def persist_document(filename: str, content: str, checksum: str, client: httpx.AsyncClient) -> tuple[dict, bool]:
    """Persiste el documento. Devuelve (documento, creado). Maneja carrera 409."""
    url = f"{settings.storage_url}/api/v1/documents/"
    payload = {"filename": filename, "content": content, "checksum": checksum}
    try:
        response = await client.post(url, json=payload, timeout=settings.storage_timeout_seconds)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al guardar documento: {str(exc)}",
        )

    if response.status_code == 201:
        return response.json(), True
    if response.status_code == 409:
        existing = await fetch_by_checksum(checksum, client)
        if existing is not None:
            return existing, False
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Conflicto al guardar el documento y no se pudo recuperarlo",
        )
    if 400 <= response.status_code < 500:
        detail = _extract_detail(response, "Error al guardar el documento")
        raise HTTPException(status_code=response.status_code, detail=detail)
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Error al guardar documento: {response.text}",
    )


async def ingest_document(file_bytes: bytes, filename: str, client: httpx.AsyncClient) -> tuple[dict, bool]:
    """Caso de uso: subir documento. Devuelve (documento, creado)."""
    checksum = compute_checksum(file_bytes)
    existing = await fetch_by_checksum(checksum, client)
    if existing is not None:
        return existing, False

    content = await extract_content(file_bytes, filename, client)
    return await persist_document(filename or "", content, checksum, client)