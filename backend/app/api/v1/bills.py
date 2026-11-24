"""M8 财务对账接口：账单导入/列表/详情/明细/匹配/封账，差异处理，结算汇总，毛利，导出。

接口清单见《接口设计》3.8（另含演示辅助：账单文件下载与毛利核算两个查询接口）。
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.finance import DiffHandleRequest
from app.services import bill_service

router = APIRouter(prefix="/bills", tags=["财务对账"])
reconcile_router = APIRouter(prefix="/reconciliations", tags=["财务对账"])


# --------------------------------------------------------------------------- #
# 账单
# --------------------------------------------------------------------------- #
@router.post("/import", summary="导入平台账单文件")
async def import_bill(
    platform_code: str = Form(..., description="平台编码"),
    shop_id: int = Form(..., description="店铺 ID"),
    bill_period: str = Form(..., description="账期，如 2026-10"),
    auto_generate: bool = Form(False, description="为真时按本地订单生成模拟账单（演示用）"),
    file: Optional[UploadFile] = File(None, description="账单文件（.csv/.xlsx）"),
    operator: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    content = await file.read() if file is not None else None
    data = bill_service.import_bill(
        session,
        platform_code=platform_code,
        shop_id=shop_id,
        bill_period=bill_period,
        file_name=file.filename if file is not None else None,
        content=content,
        auto_generate=auto_generate,
        operator=operator,
    )
    return success(data, message="账单导入成功")


@router.get("/mock-file", summary="生成并下载模拟账单文件（演示用）")
def mock_file(
    platform_code: str = Query(..., description="平台编码"),
    shop_id: int = Query(..., description="店铺 ID"),
    bill_period: str = Query(..., description="账期，如 2026-10"),
    file_type: str = Query("csv", pattern="^(csv|xlsx)$"),
    _: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    content, filename = bill_service.mock_bill_file(
        session, platform_code=platform_code, shop_id=shop_id, bill_period=bill_period, file_type=file_type
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if file_type == "xlsx"
        else "text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("", summary="账单批次列表")
def list_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    reconcile_status: str | None = None,
    bill_period: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("finance:bill")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = bill_service.list_bills(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        reconcile_status=reconcile_status,
        bill_period=bill_period,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.get("/{bill_id}", summary="账单批次详情")
def get_bill(
    bill_id: int,
    _: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    return success(bill_service.get_bill(session, bill_id))


@router.get("/{bill_id}/details", summary="账单明细列表")
def list_bill_details(
    bill_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    match_status: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    items, total = bill_service.list_bill_details(
        session, bill_id, page=page, page_size=page_size, match_status=match_status, keyword=keyword
    )
    return success_page(items, total, page, page_size)


@router.post("/{bill_id}/match", summary="触发账单与订单匹配")
def match_bill(
    bill_id: int,
    operator: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    return success(bill_service.match_bill(session, bill_id, operator), message="对账匹配完成")


@router.post("/{bill_id}/close", summary="对账期封账")
def close_bill(
    bill_id: int,
    operator: User = Depends(require_permission("finance:bill")),
    session: Session = Depends(get_db),
):
    return success(bill_service.close_bill(session, bill_id, operator), message="已封账")


# --------------------------------------------------------------------------- #
# 对账差异 / 结算 / 毛利 / 导出
# --------------------------------------------------------------------------- #
@reconcile_router.get("/differences", summary="对账差异列表")
def list_differences(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    bill_id: int | None = None,
    diff_type: str | None = None,
    handle_status: str | None = None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("finance:difference")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = bill_service.list_differences(
        session,
        page=page,
        page_size=page_size,
        bill_id=bill_id,
        diff_type=diff_type,
        handle_status=handle_status,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@reconcile_router.post("/differences/{diff_id}/handle", summary="处理对账差异")
def handle_difference(
    diff_id: int,
    payload: DiffHandleRequest,
    operator: User = Depends(require_permission("finance:difference")),
    session: Session = Depends(get_db),
):
    return success(bill_service.handle_difference(session, diff_id, payload, operator), message="差异已处理")


@reconcile_router.get("/settlements", summary="结算汇总（应收/平台费用/实收）")
def settlements(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    group_by: str = Query("platform", pattern="^(platform|shop)$"),
    _: User = Depends(require_permission("finance:settlement")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        bill_service.settlement_summary(
            session,
            start_time=start_time,
            end_time=end_time,
            platform_code=platform_code,
            shop_id=shop_id,
            group_by=group_by,
            allowed_shop_ids=allowed_shop_ids,
        )
    )


@reconcile_router.get("/profits", summary="毛利核算（订单/商品）")
def profits(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: User = Depends(require_permission("finance:profit")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        bill_service.profit_summary(
            session,
            start_time=start_time,
            end_time=end_time,
            platform_code=platform_code,
            shop_id=shop_id,
            limit=limit,
            allowed_shop_ids=allowed_shop_ids,
        )
    )


@reconcile_router.get("/export", summary="导出对账明细/差异/汇总")
def export_reconciliation(
    export_type: str = Query("detail", pattern="^(detail|difference|settlement)$"),
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    bill_id: int | None = None,
    _: User = Depends(require_permission("finance:difference")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    content, filename = bill_service.export_reconciliation(
        session,
        export_type=export_type,
        start_time=start_time,
        end_time=end_time,
        platform_code=platform_code,
        shop_id=shop_id,
        bill_id=bill_id,
        allowed_shop_ids=allowed_shop_ids,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
