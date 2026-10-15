# Ingestion - extracText

Microservicio de **orquestación de la subida de documentos**. Recibe el PDF desde el API Gateway,
calcula el checksum, consulta si ya existe en Storage, extrae el texto con el Extractor y persiste
el documento.

## Responsabilidades

- Calcular el checksum SHA-256 del PDF recibido
- Detectar documentos duplicados consultando Storage por checksum
- Orquestar la extracción de texto (Extractor) y la persistencia (Storage)
- Traducir conflictos de carrera (409) en respuestas idempotentes (200)
- Propagar los errores de validación (4xx) de los servicios aguas abajo

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.12 | Lenguaje principal |
| FastAPI | Framework web |
| httpx | Cliente HTTP async compartido en el `lifespan` |
| Uvicorn | Servidor ASGI |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/documents/` | Subir un PDF: responde 201 si es nuevo y 200 si ya existía |

## Variables de Entorno

| Variable | Descripción | Default |
|---|---|---|
| `APP_NAME` | Nombre de la aplicación | `extracText Ingestion` |
| `APP_VERSION` | Versión | `0.1.0` |
| `APP_DEBUG` | Modo debug | `false` |
| `EXTRACTOR_URL` | URL del microservicio Extractor | `http://pdf-extractxt-extractor:8000` |
| `STORAGE_URL` | URL del microservicio Storage | `http://pdf-extractxt-storage:8000` |
| `EXTRACTOR_TIMEOUT_SECONDS` | Timeout de llamadas al Extractor | `30` |
| `STORAGE_TIMEOUT_SECONDS` | Timeout de llamadas a Storage | `10` |
| `WEB_CONCURRENCY` | Procesos uvicorn por contenedor | `2` |

## Desarrollo Local

```bash
# Instalar dependencias
uv sync --all-extras

# Levantar servidor
uv run uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# Construir imagen
docker build -f dockerfile -t extractext/ingestion:latest .

# Levantar contenedor
docker run -p 8000:8000 extractext/ingestion:latest
```
