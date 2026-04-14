"""Web/static endpoints preserved from legacy Flask routes.

Important: URLs and payload structure must stay fully backward-compatible
for existing infrastructure integrations.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.core.settings import get_settings
from app.db.engine import SessionFactory
from app.db.models import AnonymOrder, OrderMess, UserTelegramInfo

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@contextmanager
def runtime_context():
    try:
        yield
    finally:
        SessionFactory.remove()


@router.get("/test/")
def test_index() -> str:
    return "Test success!!!"


def _send_file(directory: str | Path, filename: str) -> FileResponse:
    file_path = Path(directory) / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(path=file_path, filename=file_path.name)


@router.get("/static/main/js/{filename:path}")
def questions_static_main_js(filename: str):
    return _send_file(settings.main_js_folder, filename)


@router.get("/static/main/css/{filename:path}")
def questions_static_main_css(filename: str):
    return _send_file(settings.main_css_folder, filename)


@router.get("/static/main/imgs/{filename:path}")
def questions_static_main_imgs(filename: str):
    return _send_file(settings.main_imgs_folder, filename)


@router.get("/static/webappauth/js/{filename:path}")
def webappauth_static_js(filename: str):
    return _send_file(settings.webappauth_js_folder, filename)


@router.get("/static/webappauth/css/{filename:path}")
def webappauth_static_css(filename: str):
    return _send_file(settings.webappauth_css_folder, filename)


@router.get("/static/webappauth/imgs/{filename:path}")
def webappauth_static_imgs(filename: str):
    return _send_file(settings.webappauth_imgs_folder, filename)


@router.get("/static/webapp/js/{filename:path}")
def webapp_static_js(filename: str):
    return _send_file(settings.webappmain_js_folder, filename)


@router.get("/static/webapp/css/{filename:path}")
def webapp_static_css(filename: str):
    return _send_file(settings.webappmain_css_folder, filename)


@router.get("/static/webapp/imgs/{filename:path}")
def webapp_static_imgs(filename: str):
    return _send_file(settings.webappmain_imgs_folder, filename)


@router.get("/static/webappanonymviewer/js/{filename:path}")
def wappanonymviewer_static_js(filename: str):
    return _send_file(settings.wappanonymviewer_js_folder, filename)


@router.get("/static/webappanonymviewer/css/{filename:path}")
def wappanonymviewer_static_css(filename: str):
    return _send_file(settings.wappanonymviewer_css_folder, filename)


@router.get("/static/webappanonymviewer/imgs/{filename:path}")
def wappanonymviewer_static_imgs(filename: str):
    return _send_file(settings.wappanonymviewer_imgs_folder, filename)


@router.get("/static/js/{filename:path}")
def questions_static_js(filename: str):
    return _send_file(settings.js_folder, filename)


@router.get("/static/fonts/{filename:path}")
def questions_static_fonts(filename: str):
    return _send_file(settings.fonts_folder, filename)


@router.get("/static/css/{filename:path}")
def questions_static_css(filename: str):
    return _send_file(settings.css_folder, filename)


@router.get("/static/imgs/{filename:path}")
def questions_static_imgs(filename: str):
    return _send_file(settings.imgs_src, filename)


@router.get("/static/attachments/orders/{userid}/{orderid}/{filename:path}")
def show_orders_attachments(userid: int, orderid: int, filename: str):
    return _send_file(Path(settings.question_attachments_dir) / str(userid) / str(orderid), filename)


@router.get("/static/attachments/answers/{userid}/{orderid}/{filename:path}")
def show_answers_attachments(userid: int, orderid: int, filename: str):
    return _send_file(Path(settings.answer_attachments_dir) / str(userid) / str(orderid), filename)


@router.get("/main/", response_class=HTMLResponse)
def show_questions(request: Request):
    data = {
        "css_path": f"{settings.api_prefix}/static/main/css/app.css",
        "js_path": f"{settings.api_prefix}/static/main/js/app.js",
    }
    return templates.TemplateResponse(request, "questions.html", {"data": data})


@router.get("/webappauth/", response_class=HTMLResponse)
def webappauth(request: Request, webappauthtelid: str | None = Query(default=None)):
    with runtime_context():
        no_params = not bool(webappauthtelid)
        is_auth = False
        if webappauthtelid:
            is_auth = UserTelegramInfo.query.filter_by(tlgmid=str(webappauthtelid)).first() is not None

    data = {
        "no_params": no_params,
        "no_params_text": "Для авторизации не были получены все необходимые парметры. Попробуйте повторить попытку позже",
        "is_auth": is_auth,
        "usertelid": webappauthtelid,
        "title": "Авторизация",
        "already_auth_text": "Вы уже прошли процедуру авторизации",
        "webapp_js": f"{settings.api_prefix}/static/js/telegram-web-app.js",
        "app_js": f"{settings.api_prefix}/static/webappauth/js/app.js",
        "app_css": f"{settings.api_prefix}/static/webappauth/css/app.css",
    }
    return templates.TemplateResponse(request, "webappauth.html", {"data": data})


@router.get("/webappanonymviewer/", response_class=HTMLResponse)
def webapp_anonym_viewer(request: Request, webappquestionid: str | None = Query(default=None)):
    invalid = False
    with runtime_context():
        if not webappquestionid:
            invalid = True
        else:
            check_order = OrderMess.query.filter_by(id=int(webappquestionid)).first()
            if check_order is None:
                invalid = True
            else:
                check_anonym_order = AnonymOrder.query.filter_by(orderid=int(webappquestionid)).first()
                invalid = check_anonym_order is None

    data = {
        "invalid": invalid,
        "invalid_text": "Не получена необходимая информация для отображения. Повторите попытку позже",
        "title": "Просмотр вопроса",
        "webapp_js": f"{settings.api_prefix}/static/js/telegram-web-app.js",
        "app_js": f"{settings.api_prefix}/static/webappanonymviewer/js/app.js",
        "app_css": f"{settings.api_prefix}/static/webappanonymviewer/css/app.css",
    }
    return templates.TemplateResponse(request, "webappanonymviewer.html", {"data": data})


@router.get("/webapp/", response_class=HTMLResponse)
def webapp_main(request: Request):
    data = {
        "title": "Вопросы/Ответы",
        "webapp_js": f"{settings.api_prefix}/static/webapp/js/telegram-web-app.js",
        "app_js": f"{settings.api_prefix}/static/webapp/js/app.js",
        "app_css": f"{settings.api_prefix}/static/webapp/css/app.css",
    }
    return templates.TemplateResponse(request, "webapp.html", {"data": data})
