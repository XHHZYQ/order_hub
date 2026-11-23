"""M5 库存服务：库存查询/编辑、库存流水、库存共享、占用/释放/发货扣减/盘点、回写平台、预警。

防超卖核心（见《概要设计》6.4）：可售库存 = main_qty − occupied_qty；
占用采用「条件 UPDATE」实现，影响行数为 0 即库存不足（2003）；任何库存变动写 inventory_flow。
"""

from __future__ import annotations

from sqlalchemy import func as sa_func
from sqlalchemy import or_, update
from sqlmodel import Session, select

from app.core.constants import BizCode, INVENTORY_FLOW_TYPE, INVENTORY_SOURCE_TYPE
from app.core.exceptions import (
    BusinessException,
    duplicate,
    not_found,
    param_error,
    status_not_allowed,
)
from app.models.inventory import Inventory, InventoryAlert, InventoryFlow, InventoryShare
from app.models.platform import Platform, Shop
from app.models.product import PlatformSku, Product, Sku, SkuMapping
from app.services.user_service import record_operation
from app.utils.datetime_util import format_datetime, now_utc
from app.utils.pagination import normalize

_FLOW_TIME_FIELDS = ("created_at",)
_SHARE_TIME_FIELDS = ("created_at",)


def _op(operator) -> str | None:
    return operator.username if operator else None


def _fmt(data: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if field in data:
            data[field] = format_datetime(data.get(field))
    return data


def _flow_dict(row: InventoryFlow) -> dict:
    data = _fmt(row.model_dump(), _FLOW_TIME_FIELDS)
    data["flow_type_name"] = INVENTORY_FLOW_TYPE.get(row.flow_type, row.flow_type)
    data["source_type_name"] = INVENTORY_SOURCE_TYPE.get(row.source_type, row.source_type)
    return data


def _write_flow(
    session: Session,
    *,
    sku_id: int,
    sku_code: str,
    flow_type: str,
    change_qty: int,
    before_qty: int,
    after_qty: int,
    source_type: str | None = None,
    source_no: str | None = None,
    remark: str | None = None,
    operator=None,
) -> InventoryFlow:
    """写库存流水（由调用方提交事务）。"""
    row = InventoryFlow(
        sku_id=sku_id,
        sku_code=sku_code,
        flow_type=flow_type,
        change_qty=change_qty,
        before_qty=before_qty,
        after_qty=after_qty,
        source_type=source_type,
        source_no=source_no,
        remark=remark,
        operator=_op(operator),
    )
    session.add(row)
    return row


def _get_inventory(session: Session, sku_id: int) -> Inventory:
    row = session.exec(select(Inventory).where(Inventory.sku_id == sku_id)).first()
    if row is None:
        raise not_found("库存记录不存在")
    return row


def _stock_status(available: int, alert_qty, is_enabled) -> str:
    """库存状态字典：OUT 缺货 / LOW 低库存 / NORMAL 正常。"""
    if available <= 0:
        return "OUT"
    if is_enabled == 1 and alert_qty is not None and available <= alert_qty:
        return "LOW"
    return "NORMAL"


# --------------------------------------------------------------------------- #
# 库存列表 / 详情 / 主库存编辑
# --------------------------------------------------------------------------- #
def _inv_row(inv: Inventory, sku_name, spu_name, alert_qty, is_enabled) -> dict:
    available = inv.main_qty - inv.occupied_qty
    data = _fmt(inv.model_dump(), ("updated_at",))
    data.update(
        sku_name=sku_name,
        spu_name=spu_name,
        available_qty=available,
        alert_qty=alert_qty,
        is_alert=1 if (is_enabled == 1 and alert_qty is not None and available <= alert_qty) else 0,
        stock_status=_stock_status(available, alert_qty, is_enabled),
        status_name="正常" if inv.status == 1 else "停用",
    )
    return data


def list_inventory(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    keyword: str | None = None,
    status: int | None = None,
    alert_only: bool = False,
) -> tuple[list[dict], int]:
    """库存列表（可售 = 主库存 − 占用）。"""
    conditions = []
    if status is not None:
        conditions.append(Inventory.status == status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(Inventory.sku_code.like(like), Sku.sku_name.like(like)))
    if alert_only:
        conditions.append(InventoryAlert.is_enabled == 1)
        conditions.append((Inventory.main_qty - Inventory.occupied_qty) <= InventoryAlert.alert_qty)

    base = (
        select(Inventory, Sku.sku_name, Product.spu_name, InventoryAlert.alert_qty, InventoryAlert.is_enabled)
        .join(Sku, Sku.id == Inventory.sku_id, isouter=True)
        .join(Product, Product.id == Sku.spu_id, isouter=True)
        .join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id, isouter=True)
    )
    if alert_only:
        base = (
            select(Inventory, Sku.sku_name, Product.spu_name, InventoryAlert.alert_qty, InventoryAlert.is_enabled)
            .join(Sku, Sku.id == Inventory.sku_id, isouter=True)
            .join(Product, Product.id == Sku.spu_id, isouter=True)
            .join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id)
        )
    count_stmt = (
        select(sa_func.count())
        .select_from(Inventory)
        .join(Sku, Sku.id == Inventory.sku_id, isouter=True)
        .join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id, isouter=True)
        .where(*conditions)
    )

    p, s, offset = normalize(page, page_size)
    total = session.exec(count_stmt).one()
    rows = session.exec(base.where(*conditions).order_by(Inventory.id.desc()).offset(offset).limit(s)).all()
    items = [_inv_row(*row) for row in rows]
    return items, int(total)


def get_inventory(session: Session, sku_id: int) -> dict:
    """库存详情（含预警配置与共享店铺）。"""
    inv = _get_inventory(session, sku_id)
    sku = session.get(Sku, sku_id)
    spu_name = None
    if sku and sku.spu_id:
        product = session.get(Product, sku.spu_id)
        spu_name = product.spu_name if product else None
    alert = session.exec(select(InventoryAlert).where(InventoryAlert.sku_id == sku_id)).first()
    data = _inv_row(
        inv,
        sku.sku_name if sku else None,
        spu_name,
        alert.alert_qty if alert else None,
        alert.is_enabled if alert else 0,
    )
    data["shares"] = _list_shares_of_sku(session, sku_id)
    return data


def update_main_qty(session: Session, sku_id: int, payload, operator=None) -> dict:
    """编辑主库存（生成 STOCKTAKE 盘点调整流水）。"""
    inv = _get_inventory(session, sku_id)
    if payload.main_qty < inv.occupied_qty:
        raise param_error(f"主库存不能小于占用库存 {inv.occupied_qty}")
    before = inv.main_qty
    after = payload.main_qty
    inv.main_qty = after
    session.add(inv)
    _write_flow(
        session,
        sku_id=sku_id,
        sku_code=inv.sku_code,
        flow_type="STOCKTAKE",
        change_qty=after - before,
        before_qty=before,
        after_qty=after,
        source_type="STOCKTAKE",
        remark=payload.remark or "手工调整主库存",
        operator=operator,
    )
    record_operation(session, operator, "INVENTORY", "编辑", "库存", sku_id, f"调整 {inv.sku_code} 主库存 {before}→{after}")
    session.commit()
    session.refresh(inv)
    return get_inventory(session, sku_id)


# --------------------------------------------------------------------------- #
# 库存流水
# --------------------------------------------------------------------------- #
def list_flows(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    sku_id: int | None = None,
    flow_type: str | None = None,
    source_type: str | None = None,
    source_no: str | None = None,
    keyword: str | None = None,
    start_time=None,
    end_time=None,
) -> tuple[list[dict], int]:
    """库存流水列表。"""
    conditions = []
    if sku_id:
        conditions.append(InventoryFlow.sku_id == sku_id)
    if flow_type:
        conditions.append(InventoryFlow.flow_type == flow_type)
    if source_type:
        conditions.append(InventoryFlow.source_type == source_type)
    if source_no:
        conditions.append(InventoryFlow.source_no.like(f"%{source_no}%"))
    if keyword:
        conditions.append(InventoryFlow.sku_code.like(f"%{keyword}%"))
    if start_time is not None:
        conditions.append(InventoryFlow.created_at >= start_time)
    if end_time is not None:
        conditions.append(InventoryFlow.created_at <= end_time)

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(sa_func.count()).select_from(InventoryFlow).where(*conditions)).one()
    rows = session.exec(
        select(InventoryFlow).where(*conditions).order_by(InventoryFlow.id.desc()).offset(offset).limit(s)
    ).all()
    return [_flow_dict(row) for row in rows], int(total)


# --------------------------------------------------------------------------- #
# 库存共享
# --------------------------------------------------------------------------- #
def _share_row(share: InventoryShare, sku_name, shop_name, platform_name) -> dict:
    data = _fmt(share.model_dump(), _SHARE_TIME_FIELDS)
    data.update(
        sku_name=sku_name,
        shop_name=shop_name,
        platform_name=platform_name,
        status_name="启用" if share.status == 1 else "停用",
    )
    return data


def _list_shares_of_sku(session: Session, sku_id: int) -> list[dict]:
    rows = session.exec(select(InventoryShare).where(InventoryShare.sku_id == sku_id).order_by(InventoryShare.id)).all()
    return _decorate_shares(session, rows)


def _decorate_shares(session: Session, rows: list[InventoryShare]) -> list[dict]:
    if not rows:
        return []
    sku_names = {
        sku_id: name
        for sku_id, name in session.exec(
            select(Sku.id, Sku.sku_name).where(Sku.id.in_({r.sku_id for r in rows}))
        ).all()
    }
    shop_names = {
        shop_id: name
        for shop_id, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_({r.shop_id for r in rows}))
        ).all()
    }
    platform_names = {
        code: name
        for code, name in session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_({r.platform_code for r in rows if r.platform_code} or [""])
            )
        ).all()
    }
    return [
        _share_row(r, sku_names.get(r.sku_id), shop_names.get(r.shop_id), platform_names.get(r.platform_code))
        for r in rows
    ]


def list_shares(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    sku_id: int | None = None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """库存共享列表（同一 SKU 可共享给多个店铺）。"""
    conditions = []
    if sku_id:
        conditions.append(InventoryShare.sku_id == sku_id)
    if shop_id:
        conditions.append(InventoryShare.shop_id == shop_id)
    if platform_code:
        conditions.append(InventoryShare.platform_code == platform_code)
    if status is not None:
        conditions.append(InventoryShare.status == status)
    if allowed_shop_ids is not None:
        conditions.append(InventoryShare.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(sa_func.count()).select_from(InventoryShare).where(*conditions)).one()
    rows = session.exec(
        select(InventoryShare).where(*conditions).order_by(InventoryShare.id.desc()).offset(offset).limit(s)
    ).all()
    return _decorate_shares(session, rows), int(total)


def create_share(session: Session, payload, operator=None) -> dict:
    if session.exec(select(Inventory).where(Inventory.sku_id == payload.sku_id)).first() is None:
        raise not_found("库存记录不存在")
    if session.get(Shop, payload.shop_id) is None:
        raise not_found("店铺不存在")
    exists = session.exec(
        select(InventoryShare).where(
            InventoryShare.sku_id == payload.sku_id, InventoryShare.shop_id == payload.shop_id
        )
    ).first()
    if exists:
        raise duplicate("该 SKU 已共享给此店铺")
    sku = session.get(Sku, payload.sku_id)
    platform_code = payload.platform_code
    if not platform_code:
        shop = session.get(Shop, payload.shop_id)
        platform_code = shop.platform_code if shop else None
    row = InventoryShare(
        sku_id=payload.sku_id,
        sku_code=sku.sku_code if sku else "",
        shop_id=payload.shop_id,
        platform_code=platform_code,
        status=payload.status,
    )
    session.add(row)
    session.flush()
    record_operation(session, operator, "INVENTORY", "新增", "库存共享", row.id, f"SKU {row.sku_code} 共享给店铺 {row.shop_id}")
    session.commit()
    session.refresh(row)
    return _decorate_shares(session, [row])[0]


def update_share(session: Session, share_id: int, payload, operator=None) -> dict:
    row = session.get(InventoryShare, share_id)
    if not row:
        raise not_found("库存共享不存在")
    if payload.platform_code is not None:
        row.platform_code = payload.platform_code
    if payload.status is not None:
        row.status = payload.status
    session.add(row)
    record_operation(session, operator, "INVENTORY", "编辑", "库存共享", row.id, f"编辑库存共享 {row.sku_code}")
    session.commit()
    session.refresh(row)
    return _decorate_shares(session, [row])[0]


def delete_share(session: Session, share_id: int, operator=None) -> None:
    row = session.get(InventoryShare, share_id)
    if not row:
        raise not_found("库存共享不存在")
    record_operation(session, operator, "INVENTORY", "删除", "库存共享", row.id, f"删除库存共享 {row.sku_code}")
    session.delete(row)
    session.commit()


# --------------------------------------------------------------------------- #
# 占用 / 释放 / 发货扣减 / 入库（条件更新防超卖）
# --------------------------------------------------------------------------- #
def _refresh(session: Session, inv: Inventory) -> None:
    session.expire(inv)
    session.refresh(inv)


def occupy_stock(
    session: Session,
    *,
    sku_id: int,
    qty: int,
    source_no: str | None = None,
    remark: str | None = None,
    operator=None,
    source_type: str = "ORDER",
    raise_on_fail: bool = True,
) -> dict:
    """订单占用：条件 UPDATE，影响行数为 0 即库存不足（2003）。不提交事务。"""
    if qty <= 0:
        raise param_error("占用数量必须大于 0")
    inv = session.exec(select(Inventory).where(Inventory.sku_id == sku_id)).first()
    if inv is None:
        if raise_on_fail:
            raise not_found("库存记录不存在")
        return {"success": False, "reason": "库存记录不存在"}
    stmt = (
        update(Inventory)
        .where(
            Inventory.sku_id == sku_id,
            Inventory.status == 1,
            (Inventory.main_qty - Inventory.occupied_qty) >= qty,
        )
        .values(occupied_qty=Inventory.occupied_qty + qty, updated_at=sa_func.now())
    )
    result = session.execute(stmt)
    if result.rowcount == 0:
        msg = f"库存不足：{inv.sku_code} 可售 {inv.main_qty - inv.occupied_qty} < 占用 {qty}"
        if raise_on_fail:
            raise BusinessException(BizCode.STOCK_NOT_ENOUGH, msg)
        return {"success": False, "reason": "库存不足", "sku_id": sku_id, "sku_code": inv.sku_code}
    _refresh(session, inv)
    _write_flow(
        session,
        sku_id=sku_id,
        sku_code=inv.sku_code,
        flow_type="ORDER_OCCUPY",
        change_qty=0,
        before_qty=inv.main_qty,
        after_qty=inv.main_qty,
        source_type=source_type,
        source_no=source_no,
        remark=remark or f"订单占用 {qty} 件（占用库存 {inv.occupied_qty}）",
        operator=operator,
    )
    return {
        "success": True,
        "sku_id": sku_id,
        "sku_code": inv.sku_code,
        "qty": qty,
        "occupied_qty": inv.occupied_qty,
        "available_qty": inv.main_qty - inv.occupied_qty,
    }


def release_stock(
    session: Session,
    *,
    sku_id: int,
    qty: int,
    source_no: str | None = None,
    remark: str | None = None,
    operator=None,
    source_type: str = "ORDER",
    raise_on_fail: bool = True,
) -> dict:
    """订单释放占用：条件 UPDATE，占用不足则视为无可释放。不提交事务。"""
    if qty <= 0:
        raise param_error("释放数量必须大于 0")
    inv = session.exec(select(Inventory).where(Inventory.sku_id == sku_id)).first()
    if inv is None:
        if raise_on_fail:
            raise not_found("库存记录不存在")
        return {"success": False, "reason": "库存记录不存在"}
    stmt = (
        update(Inventory)
        .where(Inventory.sku_id == sku_id, Inventory.occupied_qty >= qty)
        .values(occupied_qty=Inventory.occupied_qty - qty, updated_at=sa_func.now())
    )
    result = session.execute(stmt)
    if result.rowcount == 0:
        if raise_on_fail:
            raise status_not_allowed("可释放占用不足")
        return {"success": False, "reason": "可释放占用不足", "sku_id": sku_id, "sku_code": inv.sku_code}
    _refresh(session, inv)
    _write_flow(
        session,
        sku_id=sku_id,
        sku_code=inv.sku_code,
        flow_type="ORDER_RELEASE",
        change_qty=0,
        before_qty=inv.main_qty,
        after_qty=inv.main_qty,
        source_type=source_type,
        source_no=source_no,
        remark=remark or f"订单释放 {qty} 件（占用库存 {inv.occupied_qty}）",
        operator=operator,
    )
    return {
        "success": True,
        "sku_id": sku_id,
        "sku_code": inv.sku_code,
        "qty": qty,
        "occupied_qty": inv.occupied_qty,
        "available_qty": inv.main_qty - inv.occupied_qty,
    }


def _apply_main_change(
    session: Session,
    *,
    sku_id: int,
    qty: int,
    flow_type: str,
    source_type: str | None,
    source_no: str | None,
    remark: str | None,
    operator=None,
) -> dict:
    """主库存增减（采购入库/退货入库）：条件更新 + 写流水。不提交事务。"""
    inv = session.exec(select(Inventory).where(Inventory.sku_id == sku_id)).first()
    if inv is None:
        raise not_found("库存记录不存在")
    before = inv.main_qty
    session.execute(
        update(Inventory)
        .where(Inventory.sku_id == sku_id)
        .values(main_qty=Inventory.main_qty + qty, updated_at=sa_func.now())
    )
    _refresh(session, inv)
    _write_flow(
        session,
        sku_id=sku_id,
        sku_code=inv.sku_code,
        flow_type=flow_type,
        change_qty=qty,
        before_qty=before,
        after_qty=inv.main_qty,
        source_type=source_type,
        source_no=source_no,
        remark=remark,
        operator=operator,
    )
    return {"success": True, "sku_id": sku_id, "sku_code": inv.sku_code, "qty": qty, "before_qty": before, "after_qty": inv.main_qty}


def purchase_in(session: Session, *, sku_id: int, qty: int, source_no: str | None = None, remark: str | None = None, operator=None) -> dict:
    """采购入库。"""
    return _apply_main_change(
        session, sku_id=sku_id, qty=qty, flow_type="PURCHASE_IN", source_type="PURCHASE",
        source_no=source_no, remark=remark or "采购入库", operator=operator,
    )


def return_in(session: Session, *, sku_id: int, qty: int, source_no: str | None = None, remark: str | None = None, operator=None) -> dict:
    """退货入库。"""
    return _apply_main_change(
        session, sku_id=sku_id, qty=qty, flow_type="RETURN_IN", source_type="ORDER",
        source_no=source_no, remark=remark or "退货入库", operator=operator,
    )


def ship_deduct(session: Session, *, sku_id: int, qty: int, source_no: str | None = None, remark: str | None = None, operator=None) -> dict:
    """发货扣减：减少主库存并减少占用（条件更新 + 写流水）。不提交事务。"""
    if qty <= 0:
        raise param_error("发货数量必须大于 0")
    inv = session.exec(select(Inventory).where(Inventory.sku_id == sku_id)).first()
    if inv is None:
        raise not_found("库存记录不存在")
    before = inv.main_qty
    result = session.execute(
        update(Inventory)
        .where(Inventory.sku_id == sku_id, Inventory.main_qty >= qty)
        .values(
            main_qty=Inventory.main_qty - qty,
            occupied_qty=sa_func.greatest(Inventory.occupied_qty - qty, 0),
            updated_at=sa_func.now(),
        )
    )
    if result.rowcount == 0:
        raise BusinessException(BizCode.STOCK_NOT_ENOUGH, f"库存不足，无法发货扣减：{inv.sku_code}")
    _refresh(session, inv)
    _write_flow(
        session,
        sku_id=sku_id,
        sku_code=inv.sku_code,
        flow_type="SHIP_DEDUCT",
        change_qty=-qty,
        before_qty=before,
        after_qty=inv.main_qty,
        source_type="ORDER",
        source_no=source_no,
        remark=remark or f"发货扣减 {qty} 件",
        operator=operator,
    )
    return {"success": True, "sku_id": sku_id, "sku_code": inv.sku_code, "qty": qty, "before_qty": before, "after_qty": inv.main_qty}


# --------------------------------------------------------------------------- #
# 回写平台 / 盘点 / 预警
# --------------------------------------------------------------------------- #
def push_inventory(session: Session, sku_id: int, operator=None) -> dict:
    """回写可售库存到平台规格快照。"""
    inv = _get_inventory(session, sku_id)
    available = inv.main_qty - inv.occupied_qty
    mappings = session.exec(
        select(SkuMapping).where(SkuMapping.sku_id == sku_id, SkuMapping.status == 1)
    ).all()
    shop_names = {
        shop_id: name
        for shop_id, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_({m.shop_id for m in mappings} or [-1]))
        ).all()
    }
    pushed = 0
    shop_ids: set[int] = set()
    items: list[dict] = []
    now = now_utc()
    for mapping in mappings:
        rows = session.exec(
            select(PlatformSku).where(
                PlatformSku.shop_id == mapping.shop_id, PlatformSku.platform_sku_id == mapping.platform_sku_id
            )
        ).all()
        for row in rows:
            row.platform_stock = available
            row.sync_time = now
            session.add(row)
            pushed += 1
            items.append(
                {
                    "shop_id": mapping.shop_id,
                    "shop_name": shop_names.get(mapping.shop_id),
                    "platform_code": mapping.platform_code,
                    "platform_sku_id": mapping.platform_sku_id,
                    "platform_stock": available,
                    "push_status": "成功",
                }
            )
        shop_ids.add(mapping.shop_id)
    record_operation(
        session, operator, "INVENTORY", "回写平台", "库存", sku_id, f"回写 {inv.sku_code} 可售库存 {available}，影响 {pushed} 个平台规格"
    )
    session.commit()
    return {
        "sku_id": sku_id,
        "sku_code": inv.sku_code,
        "available_qty": available,
        "pushed_count": pushed,
        "pushed_shop_count": len(shop_ids),
        "items": items,
    }


def stocktake(session: Session, payload, operator=None) -> dict:
    """盘点提交：按实盘数调整主库存并写 STOCKTAKE 流水，返回逐条明细。"""
    stocktake_no = "PD" + now_utc().strftime("%Y%m%d%H%M%S")
    items: list[dict] = []
    adjusted = 0
    gain_count = 0
    loss_count = 0
    for item in payload.items:
        inv = session.exec(select(Inventory).where(Inventory.sku_id == item.sku_id)).first()
        sku = session.get(Sku, item.sku_id)
        sku_name = sku.sku_name if sku else None
        if inv is None:
            items.append(
                {
                    "sku_id": item.sku_id,
                    "sku_code": None,
                    "sku_name": sku_name,
                    "before_qty": None,
                    "actual_qty": item.actual_qty,
                    "change_qty": 0,
                    "success": False,
                    "reason": "库存记录不存在",
                }
            )
            continue
        if item.actual_qty < inv.occupied_qty:
            items.append(
                {
                    "sku_id": item.sku_id,
                    "sku_code": inv.sku_code,
                    "sku_name": sku_name,
                    "before_qty": inv.main_qty,
                    "actual_qty": item.actual_qty,
                    "change_qty": 0,
                    "success": False,
                    "reason": f"实盘数不能小于占用库存 {inv.occupied_qty}",
                }
            )
            continue
        before = inv.main_qty
        after = item.actual_qty
        change = after - before
        inv.main_qty = after
        session.add(inv)
        _write_flow(
            session,
            sku_id=item.sku_id,
            sku_code=inv.sku_code,
            flow_type="STOCKTAKE",
            change_qty=change,
            before_qty=before,
            after_qty=after,
            source_type="STOCKTAKE",
            source_no=stocktake_no,
            remark=item.remark or "盘点调整",
            operator=operator,
        )
        adjusted += 1
        if change > 0:
            gain_count += 1
        elif change < 0:
            loss_count += 1
        items.append(
            {
                "sku_id": item.sku_id,
                "sku_code": inv.sku_code,
                "sku_name": sku_name,
                "before_qty": before,
                "actual_qty": after,
                "change_qty": change,
                "success": True,
            }
        )
    record_operation(
        session, operator, "INVENTORY", "盘点", "库存", stocktake_no, f"盘点提交：调整 {adjusted}/{len(payload.items)} 条"
    )
    session.commit()
    return {
        "stocktake_no": stocktake_no,
        "total": len(payload.items),
        "adjusted": adjusted,
        "gain_count": gain_count,
        "loss_count": loss_count,
        "items": items,
    }


def list_alerts(session: Session, *, page: int | None, page_size: int | None, keyword: str | None = None) -> tuple[list[dict], int]:
    """库存预警列表（可售 <= 安全阈值且启用）。"""
    conditions = [
        InventoryAlert.is_enabled == 1,
        (Inventory.main_qty - Inventory.occupied_qty) <= InventoryAlert.alert_qty,
    ]
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(Inventory.sku_code.like(like), Sku.sku_name.like(like)))

    count_stmt = (
        select(sa_func.count())
        .select_from(Inventory)
        .join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id)
        .join(Sku, Sku.id == Inventory.sku_id, isouter=True)
        .where(*conditions)
    )
    base = (
        select(Inventory, InventoryAlert.alert_qty, Sku.sku_name, Product.spu_name)
        .join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id)
        .join(Sku, Sku.id == Inventory.sku_id, isouter=True)
        .join(Product, Product.id == Sku.spu_id, isouter=True)
    )
    p, s, offset = normalize(page, page_size)
    total = session.exec(count_stmt).one()
    rows = session.exec(
        base.where(*conditions)
        .order_by((Inventory.main_qty - Inventory.occupied_qty).asc())
        .offset(offset)
        .limit(s)
    ).all()
    items = []
    for inv, alert_qty, sku_name, spu_name in rows:
        available = inv.main_qty - inv.occupied_qty
        items.append(
            {
                "sku_id": inv.sku_id,
                "sku_code": inv.sku_code,
                "sku_name": sku_name,
                "spu_name": spu_name,
                "main_qty": inv.main_qty,
                "occupied_qty": inv.occupied_qty,
                "available_qty": available,
                "alert_qty": alert_qty,
                "shortage_qty": max(int(alert_qty) - available, 0),
                "stock_status": _stock_status(available, alert_qty, 1),
                "updated_at": format_datetime(inv.updated_at),
            }
        )
    return items, int(total)


def list_alert_configs(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    keyword: str | None = None,
    is_enabled: int | None = None,
) -> tuple[list[dict], int]:
    """库存预警配置列表。"""
    conditions = []
    if is_enabled is not None:
        conditions.append(InventoryAlert.is_enabled == is_enabled)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(InventoryAlert.sku_code.like(like), Sku.sku_name.like(like)))

    count_stmt = (
        select(sa_func.count())
        .select_from(InventoryAlert)
        .join(Sku, Sku.id == InventoryAlert.sku_id, isouter=True)
        .where(*conditions)
    )
    base = (
        select(InventoryAlert, Sku.sku_name, Inventory.main_qty, Inventory.occupied_qty)
        .join(Sku, Sku.id == InventoryAlert.sku_id, isouter=True)
        .join(Inventory, Inventory.sku_id == InventoryAlert.sku_id, isouter=True)
    )
    p, s, offset = normalize(page, page_size)
    total = session.exec(count_stmt).one()
    rows = session.exec(base.where(*conditions).order_by(InventoryAlert.id.desc()).offset(offset).limit(s)).all()
    items = []
    for alert, sku_name, main_qty, occupied_qty in rows:
        data = _fmt(alert.model_dump(), ("updated_at",))
        available = (main_qty or 0) - (occupied_qty or 0)
        data.update(
            sku_name=sku_name,
            main_qty=main_qty,
            occupied_qty=occupied_qty,
            available_qty=available,
            is_alert=1 if (alert.is_enabled == 1 and available <= alert.alert_qty) else 0,
            stock_status=_stock_status(available, alert.alert_qty, alert.is_enabled),
            is_enabled_name="启用" if alert.is_enabled == 1 else "停用",
        )
        items.append(data)
    return items, int(total)


def update_alert_config(session: Session, alert_id: int, payload, operator=None) -> dict:
    """编辑库存预警配置。"""
    row = session.get(InventoryAlert, alert_id)
    if not row:
        raise not_found("预警配置不存在")
    if payload.alert_qty is not None:
        row.alert_qty = payload.alert_qty
    if payload.is_enabled is not None:
        row.is_enabled = payload.is_enabled
    session.add(row)
    record_operation(session, operator, "INVENTORY", "编辑", "预警配置", row.id, f"编辑 {row.sku_code} 预警阈值 {row.alert_qty}")
    session.commit()
    session.refresh(row)
    return _fmt(row.model_dump(), ("updated_at",))
