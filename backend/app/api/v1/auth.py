"""M10 认证接口：登录 / 登出 / 当前用户。"""

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.deps import get_client_ip, get_current_user, get_db
from app.core.response import success
from app.models.system import User
from app.schemas.auth import LoginRequest
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="登录")
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_db)):
    result = auth_service.login(session, payload.username, payload.password)
    user = session.get(User, result["user"]["id"])
    user_service.record_operation(
        session,
        user,
        "AUTH",
        "登录",
        "用户",
        result["user"]["id"],
        "用户登录成功",
        get_client_ip(request),
    )
    session.commit()
    return success(result)


@router.post("/logout", summary="登出")
def logout(request: Request, user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    user_service.record_operation(session, user, "AUTH", "登出", "用户", user.id, "用户登出", get_client_ip(request))
    session.commit()
    return success(None, message="已登出")


@router.get("/me", summary="当前登录用户信息")
def me(user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    return success(auth_service.build_user_profile(session, user))
