"""Domain constants used by question workflows."""

BASE_ROLE = {
    "admin": {"id": 1, "name": "Администратор"},
    "redactor": {"id": 3, "name": "Сотрудник ЕМИАС"},
    "personal": {"id": 2, "name": "Сотрудник МУ"},
}

QUESTION_STATUS = {
    "create": {"id": 1, "name": "Создано"},
    "inwork": {"id": 2, "name": "Взято в работу"},
    "received_answer": {"id": 3, "name": "Получило ответ"},
    "archive": {"id": 4, "name": "Получило ответ"},
    "trash": {"id": 5, "name": "В корзине"},
    "back_in_work": {"id": 7, "name": "Возвращено в работу"},
    "feedback": {"id": 100, "name": "Пожелания"},
    "public": {"id": 101, "name": "Опубликовано"},
}

DEFAULT_RENDER_STATUSES = ["create", "inwork", "received_answer", "back_in_work"]
NULLSPACE = {"id": 26, "title": "Не распределено", "spacekey": "nullspacekey"}
NULLROLE = {"id": 159, "name": "Другое", "emiasid": 0}
SHOW_ALL_SPACES_ITEM = {"id": 0, "title": "Показать все темы", "spacekey": ""}
EXT_DICT = {
    "imageExtension": ["png", "jpeg", "jpg"],
    "animExtension": ["gif"],
    "wordExtension": ["doc", "docx", "odf"],
    "textDocExtension": ["rtf", "txt"],
    "excelExtension": ["xlsx", "xlsm", "xlsb", "xltx", "xltm", "xls"],
    "videoExtension": ["wmv", "mp4", "mov", "avi", "flw", "swf", "mkv", "webm", "mpeg2"],
    "audioExtension": ["flac", "mp3", "wav", "wma", "aac"],
    "webExtensions": ["json"],
    "pdfExtensions": ["pdf"],
}
