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
