"""M4 SKU 映射接口：映射列表/增删改、批量维护、未匹配提醒、导入导出。"""

import csv
import io

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.constants import BizCode
from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.exceptions import BusinessException, forbidden
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.product import (
    SkuMappingBatchRequest,
    SkuMappingCreate,
    SkuMappingImportRow,
    SkuMappingUpdate,
)
from app.services import product_service

router = APIRouter(prefix="/sku-mappings", tags=["SKU映射"])

# 导入/导出统一表头
IMPORT_HEADERS = ["shop_id", "platform_code", "platform_sku_id", "sku_code", "platform_sku_name"]
IMPORT_REQUIRED = {"shop_id", "platform_sku_id", "sku_code"}


def _assert_shop_allowed(shop_id: int, allowed_shop_ids: list[int] | None) -> None:
    if allowed_shop_ids is not None and shop_id not in allowed_shop_ids:
        raise forbidden("无权操作该店铺映射")


@router.get("", summary="SKU 映射列表")
def list_sku_mappings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("product:mapping")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = product_service.list_sku_mappings(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        status=status,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


# --- 静态路径须注册在 /{mapping_id} 之前 --- #
@router.get("/unmatched", summary="未匹配平台规格列表")
def list_unmatched(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("product:mapping")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = product_service.list_unmatched(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.get("/export", summary="导出 SKU 映射")
def export_sku_mappings(
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("mapping:export")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    rows = product_service.export_sku_mappings(
        session,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        status=status,
        allowed_shop_ids=allowed_shop_ids,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORT_HEADERS)
    for row in rows:
        writer.writerow(
            [
                row.get("shop_id", ""),
                row.get("platform_code") or "",
                row.get("platform_sku_id") or "",
                row.get("sku_code") or "",
                row.get("platform_sku_name") or "",
            ]
        )
    content = ("\ufeff" + buffer.getvalue()).encode("utf-8")
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="sku_mappings.csv"'},
    )


@router.post("", summary="新增 SKU 映射")
def create_sku_mapping(
    payload: SkuMappingCreate,
    operator: User = Depends(require_permission("mapping:create")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(payload.shop_id, allowed_shop_ids)
    return success(product_service.create_sku_mapping(session, payload, operator))


@router.post("/batch", summary="批量维护 SKU 映射")
def batch_sku_mappings(
    payload: SkuMappingBatchRequest,
    operator: User = Depends(require_permission("mapping:edit")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(payload.shop_id, allowed_shop_ids)
    return success(product_service.batch_sku_mappings(session, payload, operator))


@router.post("/import", summary="导入 SKU 映射")
async def import_sku_mappings(
    file: UploadFile = File(...),
    operator: User = Depends(require_permission("mapping:import")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BusinessException(BizCode.FILE_PARSE_ERROR, f"文件解析失败：{exc}")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    if not IMPORT_REQUIRED.issubset(fieldnames):
        raise BusinessException(
            BizCode.FILE_PARSE_ERROR, "表头缺失，需包含 shop_id, platform_sku_id, sku_code"
        )
    rows: list[SkuMappingImportRow] = []
    for index, raw_row in enumerate(reader, start=2):
        try:
            shop_id = int(str(raw_row.get("shop_id", "")).strip())
        except (TypeError, ValueError):
            raise BusinessException(BizCode.FILE_PARSE_ERROR, f"第 {index} 行解析失败：shop_id 必须为整数")
        platform_sku_id = str(raw_row.get("platform_sku_id") or "").strip()
        sku_code = str(raw_row.get("sku_code") or "").strip()
        if not platform_sku_id or not sku_code:
            raise BusinessException(
                BizCode.FILE_PARSE_ERROR, f"第 {index} 行解析失败：platform_sku_id / sku_code 不能为空"
            )
        rows.append(
            SkuMappingImportRow(
                shop_id=shop_id,
                platform_code=(str(raw_row.get("platform_code") or "").strip() or None),
                platform_sku_id=platform_sku_id,
                sku_code=sku_code,
                platform_sku_name=(str(raw_row.get("platform_sku_name") or "").strip() or None),
            )
        )
    for row in rows:
        _assert_shop_allowed(row.shop_id, allowed_shop_ids)
    return success(product_service.import_sku_mappings(session, rows, operator))


@router.get("/{mapping_id}", summary="映射详情")
def get_sku_mapping(
    mapping_id: int,
    _: User = Depends(require_permission("product:mapping")),
    session: Session = Depends(get_db),
):
    return success(product_service.get_sku_mapping(session, mapping_id))


@router.put("/{mapping_id}", summary="编辑 SKU 映射")
def update_sku_mapping(
    mapping_id: int,
    payload: SkuMappingUpdate,
    operator: User = Depends(require_permission("mapping:edit")),
    session: Session = Depends(get_db),
):
    return success(product_service.update_sku_mapping(session, mapping_id, payload, operator))


@router.delete("/{mapping_id}", summary="删除 SKU 映射")
def delete_sku_mapping(
    mapping_id: int,
    operator: User = Depends(require_permission("mapping:delete")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    if allowed_shop_ids is not None:
        detail = product_service.get_sku_mapping(session, mapping_id)
        _assert_shop_allowed(detail["shop_id"], allowed_shop_ids)
    product_service.delete_sku_mapping(session, mapping_id, operator)
    return success(None)
