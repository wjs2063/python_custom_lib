from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi import FastAPI

class AppBaseException(Exception):
    status_code = 500
    message : str = "알수없는 예외가 발생하였습니다."
    detail : str = "Undefined Exception."
    code : int = 99

    def __init__(self,status_code : int | None = None, message: str | None =
    None,
                 detail:str | None = None ) -> \
            None:
        self.status_code = status_code or self.status_code
        self.message = message or self.message
        self.detail = detail or self.detail

    def to_json_response(self):
        return JSONResponse(
            status_code=self.status_code,
            content={"message": self.message,"code":self.code},
        )

class ExternalAPIError(Exception):
    """외부 API 호출 시 발생하는 기본 예외"""

    def __init__(self, service_name: str, status_code: int, detail: str):
        self.service_name = service_name
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{service_name}] {status_code}: {detail}")




class AuthTokenException(AppBaseException):
    status_code = 401
    message = "유효하지않은 토큰입니다."
    code = 50

class UnauthorizedException(AppBaseException):
    status_code = 401
    message = "인증되지않은 토큰입니다."
    code = 51

class BadRequestException(AppBaseException):
    status_code = 400
    message = "잘못된 요청입니다."
    code = 40

class NotFoundException(AppBaseException):
    status_code = 404
    message = "해당 정보를 찾을 수 없습니다"
    code = 44

class InternalServerException(AppBaseException):
    status_code = 500
    message = "Internal Server Error"
    code = 999

##

class PipelineException(AppBaseException):
    """
    파이프라인중 일부실패로 인한 에러
    """
    status_code = 500
    message = "Partial Failure"
    code = 100




def register_application_exception(app: FastAPI) -> None:
    @app.exception_handler(AppBaseException)
    def app_base_exception_handler(request: Request, exc: AppBaseException) \
            -> JSONResponse:
        return exc.to_json_response()

    @app.exception_handler(Exception)
    def undefined_exception_handler(request: Request, exc: Exception) -> (
            JSONResponse):

        # logging

        return JSONResponse(
            status_code=500,
            content={"message":"Internal Server Error","code":99},
        )





