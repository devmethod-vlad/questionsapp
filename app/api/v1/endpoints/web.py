"""Legacy web/static compatibility endpoints served by FastAPI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.core.config import Config

from questionsapp.models import AnonymOrder, OrderMess, UserTelegramInfo

router = APIRouter()

_STATIC_ROOT = Path("static")
_ORDERS_ROOT = Path(Config.QUESTION_ATTACHMENTS)
_ANSWERS_ROOT = Path(Config.ANSWER_ATTACHMENTS)


def _safe_file_response(base_dir: Path, relative_path: str) -> FileResponse:
    target = (base_dir / relative_path).resolve()
    if not str(target).startswith(str(base_dir.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(target)


@router.get("/main/")
def web_main() -> FileResponse:
    return FileResponse(_STATIC_ROOT / "main" / "index.html")


@router.get("/webapp/")
def webapp() -> FileResponse:
    return FileResponse(_STATIC_ROOT / "webappmain" / "index.html")


@router.get("/webappauth/")
def webapp_auth(webappauthtelid: str | None = Query(default=None)) -> FileResponse:
    # Compatibility check retained from Flask route to keep behavior parity.
    if webappauthtelid:
        UserTelegramInfo.query.filter_by(tlgmid=str(webappauthtelid)).first()
    return FileResponse(_STATIC_ROOT / "webappauth" / "index.html")


@router.get("/webappanonymviewer/")
def webapp_anonymviewer(webappquestionid: int | None = Query(default=None)) -> FileResponse:
    # Compatibility check retained from Flask route to keep behavior parity.
    if webappquestionid:
        check_order = OrderMess.query.filter_by(id=int(webappquestionid)).first()
        if check_order is not None:
            AnonymOrder.query.filter_by(orderid=int(webappquestionid)).first()
    return FileResponse(_STATIC_ROOT / "webappanonymviewer" / "index.html")


@router.get("/static/{file_path:path}")
def static_file(file_path: str) -> FileResponse:
    if file_path.startswith("attachments/orders/"):
        return _safe_file_response(_ORDERS_ROOT, file_path.removeprefix("attachments/orders/"))
    if file_path.startswith("attachments/answers/"):
        return _safe_file_response(_ANSWERS_ROOT, file_path.removeprefix("attachments/answers/"))
    return _safe_file_response(_STATIC_ROOT, file_path)
