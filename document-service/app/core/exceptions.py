from fastapi import HTTPException


class ServiceDocumentExceptions(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args):
        super().__init__(self.detail, *args)


class DatabaseNotUnavailableException(ServiceDocumentExceptions):
    detail = "База данных временно недоступна"


class ObjectNotFoundException(ServiceDocumentExceptions):
    detail = "Объект не найден"


class RequestNotFoundException(ServiceDocumentExceptions):
    detail = "Запрос не найден"


class UnknownExtractionSchemaException(ServiceDocumentExceptions):
    detail = "Неизвестная схема извлечения"


class ToolUseNotFoundException(ServiceDocumentExceptions):
    detail = "Модель не вернула structured output через tool_use"


class StructuredOutputValidationException(ServiceDocumentExceptions):
    detail = "Structured output не прошёл валидацию"


class LLMUnavailableError(ServiceDocumentExceptions):
    detail = "LLM service unavailable"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        Exception.__init__(self, self.detail)

    def __str__(self) -> str:
        return self.detail


class ServiceDocumentHTTPExceptions(HTTPException):
    status_code = 500
    detail = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class DatabaseNotUnavailableHTTPException(ServiceDocumentHTTPExceptions):
    status_code = 503
    detail = "База данных временно недоступна"


class RequestNotFoundHTTPException(ServiceDocumentHTTPExceptions):
    status_code = 404
    detail = "Запрос не найден"


class UnknownExtractionSchemaHTTPException(ServiceDocumentHTTPExceptions):
    status_code = 400
    detail = "Неизвестная схема извлечения"


class ToolUseNotFoundHTTPException(ServiceDocumentHTTPExceptions):
    status_code = 422
    detail = "Модель не вернула structured output через tool_use"


class StructuredOutputValidationHTTPException(ServiceDocumentHTTPExceptions):
    status_code = 422
    detail = "Structured output не прошёл валидацию"
