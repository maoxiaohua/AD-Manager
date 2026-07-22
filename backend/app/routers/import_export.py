from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.import_service import ImportService
from app.services.export_service import ExportService
from app.schemas.sync import SyncLogResponse
import logging

logger = logging.getLogger("import_export")

router = APIRouter(prefix="/api", tags=["Import/Export"])


@router.post("/import", response_model=SyncLogResponse)
async def import_file(
    file: UploadFile = File(...),
    entity_type: str = Form(..., description="computers|users|groups"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Accept CSV or Excel file. Detect format by extension."""
    content = await file.read()
    filename = file.filename.lower() if file.filename else ""

    import_service = ImportService(db)

    if filename.endswith(".csv"):
        return import_service.import_csv(content, entity_type)
    elif filename.endswith(".xlsx"):
        return import_service.import_excel(content, entity_type)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Use .csv or .xlsx",
        )


@router.get("/export/{entity_type}")
def export_data(
    entity_type: str,
    format: str = Query("csv", description="csv|xlsx"),
    search: str | None = Query(None),
    status_filter: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    logger.info(f"Export requested: entity={entity_type}, format={format}")
    export_service = ExportService(db)
    filters = {}
    if search:
        filters["search"] = search
    if status_filter:
        filters["status"] = status_filter

    if format == "csv":
        buffer = export_service.export_csv(entity_type, filters)
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={entity_type}.csv"},
        )
    elif format == "xlsx":
        buffer = export_service.export_excel(entity_type, filters)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={entity_type}.xlsx"},
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format must be csv or xlsx")


@router.get("/import/template/{entity_type}")
def download_template(
    entity_type: str,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return a blank CSV template with the correct headers."""
    export_service = ExportService(db)
    buffer = export_service.export_csv(entity_type, template=True)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type}_template.csv"},
    )
