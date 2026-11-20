"""业务异常与全局异常处理。"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import BizCode
from app.core.response import build_response


class BusinessException(Exception):
    """业务异常：接口层 / 服务层抛出，统一转成 HTTP 200 + 非 0 code。"""

    def __init__(self, code: int, message: str, http_status: int = 200):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


# 常用快捷构造
def param_error(message: str = "参数错误") -> BusinessException:
    return BusinessException(BizCode.PARAM_ERROR, message)


def unauthorized(message: str = "未登录或登录已失效") -> BusinessException:
    return BusinessException(BizCode.UNAUTHORIZED, message)


def forbidden(message: str = "无权限") -> BusinessException:
    return BusinessException(BizCode.FORBIDDEN, message)


def not_found(message: str = "资源不存在") -> BusinessException:
    return BusinessException(BizCode.NOT_FOUND, message)


def duplicate(message: str = "数据已存在") -> BusinessException:
    return BusinessException(BizCode.DUPLICATE, message)


def status_not_allowed(message: str = "当前状态不允许该操作") -> BusinessException:
    return BusinessException(BizCode.STATUS_NOT_ALLOWED, message)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(BusinessException)
    async def _business_handler(_: Request, exc: BusinessException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=build_response(code=exc.code, message=exc.message, data=None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = first.get("msg", "参数校验失败")
        message = f"参数错误：{loc} {msg}".strip()
        return JSONResponse(
            status_code=200,
            content=build_response(code=BizCode.PARAM_ERROR, message=message, data=None),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {404: BizCode.NOT_FOUND, 401: BizCode.UNAUTHORIZED, 403: BizCode.FORBIDDEN}
        code = mapping.get(exc.status_code, BizCode.UNKNOWN)
        return JSONResponse(
            status_code=200,
            content=build_response(code=code, message=str(exc.detail), data=None),
        )

    @app.exception_handler(Exception)
    async def _unknown_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=build_response(code=BizCode.UNKNOWN, message=f"服务器内部错误：{exc}", data=None),
        )
