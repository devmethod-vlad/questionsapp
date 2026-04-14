"""Question write/action handlers used by native FastAPI services.

The module mirrors legacy business logic while decoupling active service imports
from the old `app.services.legacy.questions` package.
"""

from app.services.questions_write.execaction import exec_action
from app.services.questions_write.saveanonymquestion import save_anonym_question
from app.services.questions_write.saveanswer import save_answer
from app.services.questions_write.savecombine import save_combine
from app.services.questions_write.savequestion import save_question

__all__ = [
    "exec_action",
    "save_anonym_question",
    "save_answer",
    "save_combine",
    "save_question",
]
