from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# без app: создаём объект-расширение
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],   # глобальных лимитов не задаём; вешаем на маршруты
    storage_uri="memory://"
)