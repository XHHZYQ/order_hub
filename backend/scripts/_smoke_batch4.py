"""批次4 冒烟脚本（临时验证用，用户可自行删除）。

覆盖：M3 订单处理（审核/批量审核/转发货/改价/改址/备注打标/合并/拆分/状态流转/异常订单池）、
M6 发货与物流（物流公司/待发货/面单/打单/发货/批量发货/发货单/轨迹/轨迹拉取/物流预警）、
M7 售后管理（列表/详情/同步/处理/退款/超时预警/原因分析/订单关联售后）。
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8011/api/v1"
TOKEN = ""


def _req(method, path, body=None, headers=None):
    url = BASE + path
    data = None
    hdrs = dict(headers or {})
    if TOKEN:
        hdrs["Authorization"] = "Bearer " + TOKEN
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8")), e.headers


def call(method, path, body=None):
    return _req(method, path, body=body)


def orders_by_status(status, page_size=100):
    _, r, _ = call("GET", f"/orders?status={status}&page=1&page_size={page_size}")
    assert r["code"] == 0, r
    return r["data"]["list"]


def main():
    global TOKEN
    st, r, _ = _req("POST", "/auth/login", {"username": "admin", "password": "123456"})
    assert r["code"] == 0, r
    TOKEN = r["data"]["token"]
    print("[1] 登录 OK")

    # ---------------- M3 订单处理 ---------------- #
    pending_audit = orders_by_status("PENDING_AUDIT")
    assert pending_audit, "没有待审核订单，无法验证审核"
    oid = pending_audit[0]["id"]

    _, r, _ = call("POST", f"/orders/{oid}/audit", {"action": "PASS", "reason": "冒烟审核通过"})
    assert r["code"] == 0, r
    assert r["data"]["status"] == "PENDING_SHIP", r["data"]
    print(f"[2] 单条审核 OK order={oid} 状态 → {r['data']['status']}")

    _, r, _ = call("GET", f"/orders/{oid}/status-options")
    assert r["code"] == 0 and r["data"]["options"], r
    print(f"[3] 可流转状态 OK current={r['data']['current_status']} options={r['data']['options']}")

    _, r, _ = call("POST", f"/orders/{oid}/price", {"discount_amount": 5, "reason": "冒烟改价"})
    assert r["code"] == 0, r
    print(f"[4] 改价 OK discount={r['data'].get('discount_amount')} pay={r['data'].get('pay_amount')}")

    _, rd, _ = call("GET", f"/orders/{oid}")
    det = rd["data"]
    order_det = det.get("order", det) if isinstance(det, dict) else det
    cur_city = order_det.get("receiver_city")
    print(f"[5a] 订单详情键={sorted(det.keys()) if isinstance(det, dict) else type(det).__name__}")
    new_city = "杭州市" if cur_city != "杭州市" else "广州市"
    _, r, _ = call("POST", f"/orders/{oid}/address", {"receiver_city": new_city, "reason": "冒烟改址"})
    assert r["code"] == 0, r
    print(f"[5] 改址 OK {cur_city} → {r['data'].get('receiver_city')}")

    _, r, _ = call("POST", f"/orders/{oid}/remark",
                   {"merchant_remark": "冒烟备注", "tags": ["加急", "易碎"], "append": False})
    assert r["code"] == 0, r
    print(f"[6] 备注/打标 OK tags={r['data'].get('tag_list')}")

    _, r, _ = call("GET", f"/orders/{oid}/logs")
    assert r["code"] == 0, r
    changes = r["data"].get("changes", [])
    types = sorted({c.get("change_type") for c in changes})
    print(f"[7] 变更留痕 OK changes={len(changes)} 类型={types}")
    assert {"审核", "改价", "改址"} & set(types), f"变更留痕缺失：{types}"

    # 批量审核
    batch_src = orders_by_status("PENDING_AUDIT")[:3]
    if batch_src:
        ids = [o["id"] for o in batch_src]
        _, r, _ = call("POST", "/orders/batch/audit", {"order_ids": ids, "action": "PASS", "reason": "冒烟批量审核"})
        assert r["code"] == 0, r
        print(f"[8] 批量审核 OK success={r['data'].get('success_count')} fail={r['data'].get('fail_count')}")
        _, r, _ = call("POST", "/orders/batch/remark",
                       {"order_ids": ids, "merchant_remark": "批量备注", "tags": ["团购"]})
        assert r["code"] == 0, r
        print(f"[9] 批量备注/打标 OK success={r['data'].get('success_count')}")

    # 批量转发货
    fwd_src = orders_by_status("PENDING_AUDIT")[:2]
    if fwd_src:
        _, r, _ = call("POST", "/orders/batch/forward",
                       {"order_ids": [o["id"] for o in fwd_src], "remark": "冒烟转发货"})
        assert r["code"] == 0, r
        print(f"[10] 批量转发货 OK success={r['data'].get('success_count')} fail={r['data'].get('fail_count')}")

    # 订单合并（同买家多单场景由 seed 构造）
    merged = False
    for shop_orders in _group_by_shop(orders_by_status("PENDING_SHIP", 100)):
        keys = {(o["buyer_account"], o["receiver_name"], o["receiver_phone"], o["receiver_address"]) for o in shop_orders}
        for k in keys:
            same = [o for o in shop_orders
                    if (o["buyer_account"], o["receiver_name"], o["receiver_phone"], o["receiver_address"]) == k
                    and not o.get("merge_group_no")]
            if len(same) >= 2:
                _, r, _ = call("POST", "/orders/merge",
                               {"order_ids": [o["id"] for o in same[:2]], "remark": "冒烟合并"})
                assert r["code"] == 0, r
                print(f"[11] 订单合并 OK group={r['data'].get('merge_group_no')} count={r['data'].get('order_count')}")
                merged = True
                break
        if merged:
            break
    if not merged:
        print("[11] 订单合并 跳过（未找到满足同买家同收货的待发货订单）")

    # 订单拆分（找待发货且明细数≥1 的订单）
    split_done = False
    for o in orders_by_status("PENDING_SHIP", 100):
        _, ri, _ = call("GET", f"/orders/{o['id']}/items")
        items = ri["data"]
        if not items or o.get("parent_order_no"):
            continue
        if len(items) >= 2:
            parts = [{"items": [{"item_id": items[0]["id"], "quantity": items[0]["quantity"]}]},
                     {"items": [{"item_id": items[1]["id"], "quantity": items[1]["quantity"]}]}]
        elif items[0]["quantity"] >= 2:
            q = items[0]["quantity"]
            parts = [{"items": [{"item_id": items[0]["id"], "quantity": 1}]},
                     {"items": [{"item_id": items[0]["id"], "quantity": q - 1}]}]
        else:
            continue
        _, r, _ = call("POST", f"/orders/{o['id']}/split", {"parts": parts, "remark": "冒烟拆分"})
        if r["code"] != 0:
            continue
        print(f"[12] 订单拆分 OK 父单={r['data'].get('parent_order_no')} 子单={r['data'].get('child_order_nos')}")
        split_done = True
        break
    if not split_done:
        print("[12] 订单拆分 跳过（未找到可拆分的待发货订单）")

    # 异常订单池
    _, r, _ = call("GET", "/orders/abnormal?page=1&page_size=100")
    assert r["code"] == 0, r
    abn = r["data"]["list"]
    abn_types = sorted({t for x in abn for t in x.get("abnormal_types", [])})
    print(f"[13] 异常订单池 OK total={r['data']['total']} 异常类型={abn_types}")

    # 状态流转：非法流转应被拒绝
    finished = orders_by_status("FINISHED", 1)
    if finished:
        fid = finished[0]["id"]
        _, r, _ = call("PATCH", f"/orders/{fid}/status", {"to_status": "PENDING_SHIP", "remark": "冒烟非法流转"})
        assert r["code"] != 0, f"已完成订单不应允许流转回待发货：{r}"
        print(f"[14] 非法状态流转被拒绝 OK code={r['code']} msg={r.get('message')}")

    # ---------------- M6 发货与物流 ---------------- #
    _, r, _ = call("GET", "/logistics-companies")
    assert r["code"] == 0 and r["data"], r
    print(f"[15] 物流公司 OK 共{len(r['data'])}家 示例={r['data'][0].get('company_name')}")

    _, r, _ = call("GET", "/shipments/pending?page=1&page_size=100")
    assert r["code"] == 0, r
    pend = r["data"]["list"]
    assert pend, "没有待发货订单"
    print(f"[16] 待发货列表 OK total={r['data']['total']}")

    pick_ids = [o["id"] for o in pend[:3]]
    _, r, _ = call("POST", "/shipments/waybill", {"order_ids": pick_ids})
    assert r["code"] == 0, r
    wb = r["data"]
    wb_items = wb.get("items", wb) if isinstance(wb, dict) else wb
    print(f"[17] 获取面单 OK {json.dumps(wb_items, ensure_ascii=False)[:220]}")

    _, r, _ = call("POST", "/shipments/print", {"order_ids": pick_ids})
    assert r["code"] == 0, r
    print(f"[18] 批量打单 OK {json.dumps(r['data'], ensure_ascii=False)[:220]}")

    # 单笔发货
    _, r, _ = call("POST", "/shipments", {"order_id": pick_ids[0]})
    assert r["code"] == 0, r
    ship = r["data"]
    sid = ship["id"]
    print(f"[19] 发货 OK shipment_no={ship.get('shipment_no')} waybill={ship.get('waybill_no')} status={ship.get('status')}")

    # 批量发货
    if len(pick_ids) >= 2:
        _, r, _ = call("POST", "/shipments/batch", {"order_ids": pick_ids[1:2]})
        assert r["code"] == 0, r
        print(f"[20] 批量发货 OK success={r['data'].get('success_count')} fail={r['data'].get('fail_count')}")

    _, r, _ = call("GET", "/shipments?page=1&page_size=100")
    assert r["code"] == 0, r
    ships = r["data"]["list"]
    statuses = sorted({x.get("status") for x in ships})
    print(f"[21] 发货单列表 OK total={r['data']['total']} 状态覆盖={statuses}")

    _, r, _ = call("GET", f"/shipments/{sid}")
    assert r["code"] == 0, r
    print(f"[22] 发货单详情 OK order_no={r['data'].get('order_no')} company={r['data'].get('logistics_company_name')}")

    _, r, _ = call("GET", f"/shipments/{sid}/traces")
    assert r["code"] == 0, r
    tr = r["data"]
    print(f"[23] 物流轨迹 OK 共{len(tr)}条 最新={tr[-1].get('trace_desc') if tr else None}")

    _, r, _ = call("POST", f"/shipments/{sid}/sync-trace")
    assert r["code"] == 0, r
    print(f"[24] 拉取轨迹 OK 新增={r['data'].get('added')} status={r['data'].get('status')}")

    _, r, _ = call("GET", "/shipments/alerts?page=1&page_size=100")
    assert r["code"] == 0, r
    alerts = r["data"]["list"]
    print(f"[25] 物流异常预警 OK total={r['data']['total']} 示例={alerts[0].get('alert_reason') if alerts else '无'}")

    # ---------------- M7 售后管理 ---------------- #
    _, r, _ = call("GET", "/after-sales?page=1&page_size=100")
    assert r["code"] == 0, r
    ass = r["data"]["list"]
    assert ass, "售后单列表为空，seed 未覆盖 M7"
    as_status = sorted({x.get("status") for x in ass})
    as_type = sorted({x.get("type") for x in ass})
    print(f"[26] 售后单列表 OK total={r['data']['total']} 状态={as_status} 类型={as_type}")

    _, r, _ = call("GET", "/after-sales/analysis")
    assert r["code"] == 0, r
    print(f"[27] 售后原因分析 OK {json.dumps(r['data'], ensure_ascii=False)[:220]}")

    _, r, _ = call("GET", "/after-sales/alerts?page=1&page_size=100")
    assert r["code"] == 0, r
    print(f"[28] 售后超时预警 OK total={r['data']['total']}")

    # 售后处理：选一条待处理退款单 → 同意 → 退货入库
    target = next((x for x in ass if x.get("status") == "PENDING"), ass[0])
    asid = target["id"]
    _, r, _ = call("GET", f"/after-sales/{asid}")
    assert r["code"] == 0, r
    print(f"[29] 售后详情 OK no={r['data'].get('after_sale_no')} logs={len(r['data'].get('logs', []))}")

    _, r, _ = call("POST", f"/after-sales/{asid}/handle", {"action": "同意", "content": "冒烟同意"})
    assert r["code"] == 0, r
    print(f"[30] 售后处理(同意) OK status={r['data'].get('status')}")

    _, r, _ = call("POST", f"/after-sales/{asid}/refund", {"refund_amount": 10, "refund_status": "SUCCESS"})
    assert r["code"] == 0, r
    print(f"[31] 退款同步 OK refund={r['data'].get('refund_amount')} refund_status={r['data'].get('refund_status')}")

    # 退货入库（另选一条待处理的退货退款单，避免与上面状态冲突）
    _, rl, _ = call("GET", "/after-sales?page=1&page_size=100")
    restock = next((x for x in rl["data"]["list"]
                    if x.get("status") == "PENDING" and x.get("type") == "RETURN_REFUND"), None)
    if restock:
        _, r, _ = call("POST", f"/after-sales/{restock['id']}/handle", {"action": "同意", "content": "冒烟同意退货"})
        assert r["code"] == 0, r
        _, r, _ = call("POST", f"/after-sales/{restock['id']}/handle",
                       {"action": "退货入库", "content": "冒烟退货入库", "goods_returned": True})
        assert r["code"] == 0, r
        print(f"[32] 售后处理(退货入库/回补库存) OK status={r['data'].get('status')} returned={r['data'].get('goods_returned')}")
    else:
        print("[32] 退货入库 跳过（无待处理的退货退款单）")

    # 订单关联售后
    as_order_id = target.get("order_id")
    _, r, _ = call("GET", f"/orders/{as_order_id}/after-sales")
    assert r["code"] == 0, r
    print(f"[33] 订单关联售后 OK order={as_order_id} 关联{len(r['data'])}条")

    # 手动同步售后
    _, r, _ = call("POST", "/after-sales/sync", {"shop_id": target.get("shop_id")})
    assert r["code"] == 0, r
    print(f"[34] 同步售后 OK {json.dumps(r['data'], ensure_ascii=False)[:200]}")

    print("=== 批次4 冒烟全部通过 ===")


def _group_by_shop(rows):
    groups = {}
    for o in rows:
        groups.setdefault(o.get("shop_id"), []).append(o)
    return list(groups.values())


if __name__ == "__main__":
    main()
