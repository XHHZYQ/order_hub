"""M4 商品与 SKU 映射服务：本地商品/SKU 维护、平台商品查询、SKU 映射维护与导入导出。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.core.exceptions import BusinessException, duplicate, not_found
from app.models.platform import Platform, Shop
from app.models.product import PlatformProduct, PlatformSku, Product, Sku, SkuMapping
from app.services.user_service import record_operation
from app.utils.datetime_util import format_datetime
from app.utils.pagination import normalize

_PRODUCT_TIME_FIELDS = ("created_at", "updated_at")
_PLATFORM_TIME_FIELDS = ("sync_time", "created_at")
_MAPPING_TIME_FIELDS = ("created_at", "updated_at")


def _fmt(data: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if field in data:
            data[field] = format_datetime(data.get(field))
    return data


def _to_decimal(value) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal("0")


# --------------------------------------------------------------------------- #
# 本地商品 / SKU
# --------------------------------------------------------------------------- #
def _sku_counts(session: Session, spu_ids: list[int]) -> dict[int, int]:
    if not spu_ids:
        return {}
    rows = session.exec(
        select(Sku.spu_id, func.count())
        .where(Sku.spu_id.in_(spu_ids), Sku.is_deleted == 0)
        .group_by(Sku.spu_id)
    ).all()
    return {int(spu_id): int(cnt) for spu_id, cnt in rows}


def _sku_dict(row: Sku) -> dict:
    data = _fmt(row.model_dump(), _PRODUCT_TIME_FIELDS)
    data["status_name"] = "启用" if row.status == 1 else "停用"
    return data


def list_products(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    keyword: str | None = None,
    category_name: str | None = None,
    brand: str | None = None,
    status: int | None = None,
) -> tuple[list[dict], int]:
    """本地商品（SPU）列表。"""
    conditions = [Product.is_deleted == 0]
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(Product.spu_code.like(like), Product.spu_name.like(like)))
    if category_name:
        conditions.append(Product.category_name == category_name)
    if brand:
        conditions.append(Product.brand == brand)
    if status is not None:
        conditions.append(Product.status == status)

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Product).where(*conditions)).one()
    rows = session.exec(
        select(Product).where(*conditions).order_by(Product.id.desc()).offset(offset).limit(s)
    ).all()
    counts = _sku_counts(session, [r.id for r in rows])
    items = []
    for row in rows:
        data = _fmt(row.model_dump(), _PRODUCT_TIME_FIELDS)
        data["status_name"] = "启用" if row.status == 1 else "停用"
        data["sku_count"] = counts.get(row.id, 0)
        items.append(data)
    return items, int(total)


def get_product(session: Session, product_id: int) -> dict:
    """商品详情（含 SKU 列表）。"""
    row = session.get(Product, product_id)
    if not row or row.is_deleted == 1:
        raise not_found("商品不存在")
    data = _fmt(row.model_dump(), _PRODUCT_TIME_FIELDS)
    data["status_name"] = "启用" if row.status == 1 else "停用"
    data["skus"] = list_skus(session, product_id)
    return data


def create_product(session: Session, payload, operator=None) -> dict:
    if session.exec(select(Product).where(Product.spu_code == payload.spu_code)).first():
        raise duplicate("SPU 编码已存在")
    row = Product(
        spu_code=payload.spu_code,
        spu_name=payload.spu_name,
        category_name=payload.category_name,
        brand=payload.brand,
        unit=payload.unit,
        status=payload.status,
        remark=payload.remark,
    )
    session.add(row)
    session.flush()
    record_operation(session, operator, "PRODUCT", "新增", "商品", row.id, f"新增商品 {row.spu_code}")
    session.commit()
    session.refresh(row)
    return get_product(session, row.id)


def update_product(session: Session, product_id: int, payload, operator=None) -> dict:
    row = session.get(Product, product_id)
    if not row or row.is_deleted == 1:
        raise not_found("商品不存在")
    for field in ("spu_name", "category_name", "brand", "unit", "status", "remark"):
        value = getattr(payload, field)
        if value is not None:
            setattr(row, field, value)
    session.add(row)
    record_operation(session, operator, "PRODUCT", "编辑", "商品", row.id, f"编辑商品 {row.spu_code}")
    session.commit()
    session.refresh(row)
    return get_product(session, row.id)


def delete_product(session: Session, product_id: int, operator=None) -> None:
    row = session.get(Product, product_id)
    if not row or row.is_deleted == 1:
        raise not_found("商品不存在")
    row.is_deleted = 1
    session.add(row)
    skus = session.exec(select(Sku).where(Sku.spu_id == product_id, Sku.is_deleted == 0)).all()
    for sku in skus:
        sku.is_deleted = 1
        session.add(sku)
    record_operation(session, operator, "PRODUCT", "删除", "商品", row.id, f"删除商品 {row.spu_code}")
    session.commit()


def list_skus(session: Session, product_id: int) -> list[dict]:
    rows = session.exec(
        select(Sku).where(Sku.spu_id == product_id, Sku.is_deleted == 0).order_by(Sku.id)
    ).all()
    return [_sku_dict(row) for row in rows]


def _get_sku(session: Session, sku_id: int) -> Sku:
    row = session.get(Sku, sku_id)
    if not row or row.is_deleted == 1:
        raise not_found("SKU 不存在")
    return row


def _resolve_sku_by_code(session: Session, sku_code: str) -> Sku:
    """按本地 SKU 编码解析 Sku，未找到抛 1004。"""
    row = session.exec(select(Sku).where(Sku.sku_code == sku_code, Sku.is_deleted == 0)).first()
    if row is None:
        raise not_found(f"本地 SKU 不存在：{sku_code}")
    return row


def create_sku(session: Session, product_id: int, payload, operator=None) -> dict:
    product = session.get(Product, product_id)
    if not product or product.is_deleted == 1:
        raise not_found("商品不存在")
    if session.exec(select(Sku).where(Sku.sku_code == payload.sku_code)).first():
        raise duplicate("SKU 编码已存在")
    row = Sku(
        sku_code=payload.sku_code,
        spu_id=product_id,
        sku_name=payload.sku_name,
        spec_desc=payload.spec_desc,
        cost_price=_to_decimal(payload.cost_price),
        sale_price=_to_decimal(payload.sale_price),
        status=payload.status,
    )
    session.add(row)
    session.flush()
    record_operation(session, operator, "PRODUCT", "新增", "SKU", row.id, f"新增 SKU {row.sku_code}")
    session.commit()
    session.refresh(row)
    return _sku_dict(row)


def update_sku(session: Session, sku_id: int, payload, operator=None) -> dict:
    row = _get_sku(session, sku_id)
    for field in ("sku_name", "spec_desc", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(row, field, value)
    if payload.cost_price is not None:
        row.cost_price = _to_decimal(payload.cost_price)
    if payload.sale_price is not None:
        row.sale_price = _to_decimal(payload.sale_price)
    session.add(row)
    record_operation(session, operator, "PRODUCT", "编辑", "SKU", row.id, f"编辑 SKU {row.sku_code}")
    session.commit()
    session.refresh(row)
    return _sku_dict(row)


def delete_sku(session: Session, sku_id: int, operator=None) -> None:
    row = _get_sku(session, sku_id)
    row.is_deleted = 1
    session.add(row)
    record_operation(session, operator, "PRODUCT", "删除", "SKU", row.id, f"删除 SKU {row.sku_code}")
    session.commit()


# --------------------------------------------------------------------------- #
# 平台商品 / 规格
# --------------------------------------------------------------------------- #
def _shop_names(session: Session, shop_ids: list[int]) -> dict[int, str]:
    if not shop_ids:
        return {}
    rows = session.exec(select(Shop.id, Shop.shop_name).where(Shop.id.in_(shop_ids))).all()
    return {int(sid): name for sid, name in rows}


def _platform_names(session: Session, codes: list[str | None]) -> dict[str, str]:
    """按平台编码取平台名称，用于列表/详情展示。"""
    valid = {c for c in codes if c}
    if not valid:
        return {}
    rows = session.exec(
        select(Platform.platform_code, Platform.platform_name).where(Platform.platform_code.in_(valid))
    ).all()
    return {code: name for code, name in rows}


def list_platform_products(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """平台商品列表。"""
    conditions = []
    if shop_id:
        conditions.append(PlatformProduct.shop_id == shop_id)
    if platform_code:
        conditions.append(PlatformProduct.platform_code == platform_code)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(PlatformProduct.product_title.like(like), PlatformProduct.platform_product_id.like(like))
        )
    if allowed_shop_ids is not None:
        conditions.append(PlatformProduct.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(PlatformProduct).where(*conditions)).one()
    rows = session.exec(
        select(PlatformProduct)
        .where(*conditions)
        .order_by(PlatformProduct.id.desc())
        .offset(offset)
        .limit(s)
    ).all()

    product_ids = [r.id for r in rows]
    sku_counts: dict[int, int] = {}
    if product_ids:
        counts = session.exec(
            select(PlatformSku.platform_product_id, func.count())
            .where(PlatformSku.platform_product_id.in_(product_ids))
            .group_by(PlatformSku.platform_product_id)
        ).all()
        sku_counts = {int(pid): int(cnt) for pid, cnt in counts}
    shop_names = _shop_names(session, [r.shop_id for r in rows])
    platform_names = _platform_names(session, [r.platform_code for r in rows])

    items = []
    for row in rows:
        data = _fmt(row.model_dump(), _PLATFORM_TIME_FIELDS)
        data["shop_name"] = shop_names.get(row.shop_id)
        data["platform_name"] = platform_names.get(row.platform_code)
        data["sku_count"] = sku_counts.get(row.id, 0)
        items.append(data)
    return items, int(total)


def get_platform_product(session: Session, platform_product_id: int) -> dict:
    """平台商品详情（含平台规格）。"""
    row = session.get(PlatformProduct, platform_product_id)
    if not row:
        raise not_found("平台商品不存在")
    data = _fmt(row.model_dump(), _PLATFORM_TIME_FIELDS)
    data["shop_name"] = _shop_names(session, [row.shop_id]).get(row.shop_id)
    data["platform_name"] = _platform_names(session, [row.platform_code]).get(row.platform_code)
    skus = session.exec(
        select(PlatformSku)
        .where(PlatformSku.platform_product_id == platform_product_id)
        .order_by(PlatformSku.id)
    ).all()
    data["skus"] = [_fmt(item.model_dump(), _PLATFORM_TIME_FIELDS) for item in skus]
    return data


# --------------------------------------------------------------------------- #
# SKU 映射
# --------------------------------------------------------------------------- #
def _platform_code_of_shop(session: Session, shop_id: int) -> str | None:
    shop = session.get(Shop, shop_id)
    return shop.platform_code if shop else None


def _sync_platform_sku_matched(session: Session, shop_id: int, platform_sku_id: str, matched: int) -> None:
    rows = session.exec(
        select(PlatformSku).where(
            PlatformSku.shop_id == shop_id, PlatformSku.platform_sku_id == str(platform_sku_id)
        )
    ).all()
    for row in rows:
        row.is_matched = matched
        session.add(row)


def find_mapping(session: Session, shop_id: int, platform_sku_id: str | None) -> SkuMapping | None:
    """按 (shop_id, platform_sku_id) 查启用映射（供订单同步匹配本地 SKU）。"""
    if not platform_sku_id:
        return None
    return session.exec(
        select(SkuMapping).where(
            SkuMapping.shop_id == shop_id,
            SkuMapping.platform_sku_id == str(platform_sku_id),
            SkuMapping.status == 1,
        )
    ).first()


def _mapping_dict(row: SkuMapping, shop_name: str | None, platform_name: str | None, sku_name: str | None) -> dict:
    data = _fmt(row.model_dump(), _MAPPING_TIME_FIELDS)
    data["shop_name"] = shop_name
    data["platform_name"] = platform_name
    data["sku_name"] = sku_name
    data["status_name"] = "启用" if row.status == 1 else "停用"
    return data


def _name_maps(session: Session, rows: list[SkuMapping]) -> tuple[dict[int, str], dict[str, str], dict[int, str]]:
    shop_names = _shop_names(session, [r.shop_id for r in rows])
    platform_names = {
        code: name
        for code, name in session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_({r.platform_code for r in rows} or [""])
            )
        ).all()
    }
    sku_names = {
        sku_id: name
        for sku_id, name in session.exec(
            select(Sku.id, Sku.sku_name).where(Sku.id.in_({r.sku_id for r in rows} or [-1]))
        ).all()
    }
    return shop_names, platform_names, sku_names


def list_sku_mappings(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    status: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """SKU 映射列表。"""
    conditions = []
    if shop_id:
        conditions.append(SkuMapping.shop_id == shop_id)
    if platform_code:
        conditions.append(SkuMapping.platform_code == platform_code)
    if status is not None:
        conditions.append(SkuMapping.status == status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                SkuMapping.platform_sku_id.like(like),
                SkuMapping.platform_sku_name.like(like),
                SkuMapping.sku_code.like(like),
            )
        )
    if allowed_shop_ids is not None:
        conditions.append(SkuMapping.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(SkuMapping).where(*conditions)).one()
    rows = session.exec(
        select(SkuMapping).where(*conditions).order_by(SkuMapping.id.desc()).offset(offset).limit(s)
    ).all()
    shop_names, platform_names, sku_names = _name_maps(session, rows)
    items = [
        _mapping_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), sku_names.get(r.sku_id))
        for r in rows
    ]
    return items, int(total)


def get_sku_mapping(session: Session, mapping_id: int) -> dict:
    row = session.get(SkuMapping, mapping_id)
    if not row:
        raise not_found("映射不存在")
    shop_names, platform_names, sku_names = _name_maps(session, [row])
    return _mapping_dict(row, shop_names.get(row.shop_id), platform_names.get(row.platform_code), sku_names.get(row.sku_id))


def create_sku_mapping(session: Session, payload, operator=None) -> dict:
    sku = _resolve_sku_by_code(session, payload.sku_code)
    exists = session.exec(
        select(SkuMapping).where(
            SkuMapping.shop_id == payload.shop_id, SkuMapping.platform_sku_id == payload.platform_sku_id
        )
    ).first()
    if exists:
        raise duplicate("该平台 SKU 已存在映射")
    row = SkuMapping(
        platform_code=payload.platform_code or _platform_code_of_shop(session, payload.shop_id),
        shop_id=payload.shop_id,
        platform_sku_id=payload.platform_sku_id,
        platform_sku_name=payload.platform_sku_name or sku.sku_name,
        sku_id=sku.id,
        sku_code=sku.sku_code,
        status=payload.status,
        remark=payload.remark,
    )
    session.add(row)
    session.flush()
    _sync_platform_sku_matched(session, row.shop_id, row.platform_sku_id, 1)
    record_operation(session, operator, "MAPPING", "新增", "SKU映射", row.id, f"新增映射 {row.platform_sku_id}")
    session.commit()
    session.refresh(row)
    return get_sku_mapping(session, row.id)


def update_sku_mapping(session: Session, mapping_id: int, payload, operator=None) -> dict:
    row = session.get(SkuMapping, mapping_id)
    if not row:
        raise not_found("映射不存在")
    if payload.platform_sku_name is not None:
        row.platform_sku_name = payload.platform_sku_name
    if payload.status is not None:
        row.status = payload.status
    if payload.remark is not None:
        row.remark = payload.remark
    if payload.sku_code is not None:
        sku = _resolve_sku_by_code(session, payload.sku_code)
        row.sku_id = sku.id
        row.sku_code = sku.sku_code
    elif payload.sku_id is not None:
        sku = _get_sku(session, payload.sku_id)
        row.sku_id = sku.id
        row.sku_code = sku.sku_code
    session.add(row)
    record_operation(session, operator, "MAPPING", "编辑", "SKU映射", row.id, f"编辑映射 {row.platform_sku_id}")
    session.commit()
    session.refresh(row)
    return get_sku_mapping(session, row.id)


def delete_sku_mapping(session: Session, mapping_id: int, operator=None) -> None:
    row = session.get(SkuMapping, mapping_id)
    if not row:
        raise not_found("映射不存在")
    record_operation(session, operator, "MAPPING", "删除", "SKU映射", row.id, f"删除映射 {row.platform_sku_id}")
    _sync_platform_sku_matched(session, row.shop_id, row.platform_sku_id, 0)
    session.delete(row)
    session.commit()


def _upsert_mapping(session: Session, *, shop_id: int, platform_code: str | None, platform_sku_id: str, sku: Sku, platform_sku_name: str | None = None, remark: str | None = None) -> bool:
    """按 (shop_id, platform_sku_id) 覆盖写入映射，返回是否新建。"""
    row = session.exec(
        select(SkuMapping).where(SkuMapping.shop_id == shop_id, SkuMapping.platform_sku_id == platform_sku_id)
    ).first()
    created = row is None
    if created:
        row = SkuMapping(
            platform_code=platform_code or _platform_code_of_shop(session, shop_id),
            shop_id=shop_id,
            platform_sku_id=platform_sku_id,
            platform_sku_name=platform_sku_name or sku.sku_name,
            sku_id=sku.id,
            sku_code=sku.sku_code,
            status=1,
            remark=remark,
        )
    else:
        row.sku_id = sku.id
        row.sku_code = sku.sku_code
        if platform_sku_name:
            row.platform_sku_name = platform_sku_name
        if remark is not None:
            row.remark = remark
    session.add(row)
    _sync_platform_sku_matched(session, shop_id, platform_sku_id, 1)
    return created


def batch_sku_mappings(session: Session, payload, operator=None) -> dict:
    """批量维护映射（按 (shop_id, platform_sku_id) 覆盖，逐条容错）。"""
    total = success = 0
    errors: list[dict] = []
    for index, item in enumerate(payload.items, start=1):
        total += 1
        try:
            sku = _resolve_sku_by_code(session, item.sku_code)
        except BusinessException as exc:
            errors.append({"row": index, "platform_sku_id": item.platform_sku_id, "reason": exc.message})
            continue
        _upsert_mapping(
            session,
            shop_id=payload.shop_id,
            platform_code=payload.platform_code,
            platform_sku_id=item.platform_sku_id,
            sku=sku,
            platform_sku_name=item.platform_sku_name,
            remark=item.remark,
        )
        success += 1
    record_operation(
        session, operator, "MAPPING", "批量维护", "SKU映射", None, f"批量维护映射：成功 {success} 条，失败 {len(errors)} 条"
    )
    session.commit()
    return {"total": total, "success_count": success, "fail_count": len(errors), "errors": errors}


def list_unmatched(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """未匹配的平台规格列表（platform_sku 无对应映射）。"""
    sub = select(SkuMapping.id).where(
        SkuMapping.shop_id == PlatformSku.shop_id,
        SkuMapping.platform_sku_id == PlatformSku.platform_sku_id,
    )
    conditions = [~sub.exists()]
    if shop_id:
        conditions.append(PlatformSku.shop_id == shop_id)
    if platform_code:
        conditions.append(PlatformSku.platform_code == platform_code)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                PlatformSku.platform_sku_id.like(like),
                PlatformSku.sku_name.like(like),
                PlatformSku.outer_sku_code.like(like),
            )
        )
    if allowed_shop_ids is not None:
        conditions.append(PlatformSku.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(PlatformSku).where(*conditions)).one()
    rows = session.exec(
        select(PlatformSku).where(*conditions).order_by(PlatformSku.id.desc()).offset(offset).limit(s)
    ).all()
    shop_names = _shop_names(session, [r.shop_id for r in rows])
    items = []
    for row in rows:
        data = _fmt(row.model_dump(), _PLATFORM_TIME_FIELDS)
        data["shop_name"] = shop_names.get(row.shop_id)
        items.append(data)
    return items, int(total)


def import_sku_mappings(session: Session, rows, operator=None) -> dict:
    """导入映射（接收已解析好的行列表，按本地 SKU 编码建立映射，逐行容错）。"""
    total = success = 0
    errors: list[dict] = []
    for index, item in enumerate(rows, start=1):
        total += 1
        sku = session.exec(
            select(Sku).where(Sku.sku_code == item.sku_code, Sku.is_deleted == 0)
        ).first()
        if sku is None:
            errors.append({"row": index, "platform_sku_id": item.platform_sku_id, "reason": f"本地 SKU 不存在：{item.sku_code}"})
            continue
        _upsert_mapping(
            session,
            shop_id=item.shop_id,
            platform_code=item.platform_code,
            platform_sku_id=item.platform_sku_id,
            sku=sku,
            platform_sku_name=item.platform_sku_name,
        )
        success += 1
    record_operation(
        session, operator, "MAPPING", "导入", "SKU映射", None, f"导入映射：成功 {success} 条，失败 {len(errors)} 条"
    )
    session.commit()
    return {"total": total, "success_count": success, "fail_count": len(errors), "errors": errors}


def export_sku_mappings(
    session: Session,
    *,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    status: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> list[dict]:
    """导出映射（不分页，沿用列表筛选条件）。"""
    conditions = []
    if shop_id:
        conditions.append(SkuMapping.shop_id == shop_id)
    if platform_code:
        conditions.append(SkuMapping.platform_code == platform_code)
    if status is not None:
        conditions.append(SkuMapping.status == status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                SkuMapping.platform_sku_id.like(like),
                SkuMapping.platform_sku_name.like(like),
                SkuMapping.sku_code.like(like),
            )
        )
    if allowed_shop_ids is not None:
        conditions.append(SkuMapping.shop_id.in_(allowed_shop_ids or [-1]))
    rows = session.exec(select(SkuMapping).where(*conditions).order_by(SkuMapping.id)).all()
    shop_names, platform_names, sku_names = _name_maps(session, rows)
    return [
        _mapping_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), sku_names.get(r.sku_id))
        for r in rows
    ]
