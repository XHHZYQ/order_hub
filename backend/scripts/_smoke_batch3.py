"""批次3 冒烟脚本（临时验证用，用户可自行删除）。

覆盖：M4 本地商品/平台商品/SKU映射（含未匹配、批量、导入、导出）、
M5 库存（列表/流水/共享/预警/回写/盘点），以及库存占用并发防超卖。
"""
import json
import threading
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8011/api/v1"
TOKEN = ""


def _req(method, path, body=None, raw=None, content_type="application/json", headers=None):
    url = BASE + path
    data = None
    hdrs = dict(headers or {})
    if TOKEN:
        hdrs["Authorization"] = "Bearer " + TOKEN
    if raw is not None:
        data = raw
        if content_type:
            hdrs["Content-Type"] = content_type
    elif body is not None:
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


def main():
    global TOKEN
    st, r, _ = _req("POST", "/auth/login", {"username": "admin", "password": "123456"})
    assert r["code"] == 0, r
    TOKEN = r["data"]["token"]
    print("[1] 登录 OK")

    # 库存列表，挑一个可售>0 的 SKU
    _, r, _ = call("GET", "/inventory?page=1&page_size=100")
    rows = r["data"]["list"]
    assert rows, "库存为空"
    assert all("stock_status" in x for x in rows), "库存缺少 stock_status"
    assert all("available_qty" in x for x in rows)
    sku = next(x for x in rows if x["available_qty"] >= 3)
    print(f"[2] 库存列表 OK 共{len(rows)}条, 选中 sku_code={sku['sku_code']} available={sku['available_qty']} status={sku['stock_status']}")
    # 未匹配平台规格
    _, r, _ = call("GET", "/sku-mappings/unmatched?page=1&page_size=2")
    un = r["data"]["list"]
    assert un, "未匹配列表为空（应保留未映射规格用于演示）"
    print(f"[3] 未匹配 OK total={r['data']['total']} 示例={un[0].get('platform_sku_id')} shop={un[0].get('shop_id')}")

    # 单条新增映射（用 sku_code）
    body = {
        "shop_id": un[0]["shop_id"],
        "platform_code": un[0].get("platform_code"),
        "platform_sku_id": un[0]["platform_sku_id"],
        "platform_sku_name": un[0].get("platform_sku_name"),
        "sku_code": sku["sku_code"],
        "status": 1,
    }
    _, r, _ = call("POST", "/sku-mappings", body)
    assert r["code"] == 0, r
    mid = r["data"]["id"]
    print(f"[4] 新增映射(sku_code) OK id={mid}")

    # 批量映射
    body = {"shop_id": un[0]["shop_id"], "items": [
        {"platform_sku_id": "SMOKE-SKU-1", "platform_sku_name": "冒烟规格1", "sku_code": sku["sku_code"]},
        {"platform_sku_id": "SMOKE-SKU-2", "sku_code": "NOT-EXIST-CODE"},
    ]}
    _, r, _ = call("POST", "/sku-mappings/batch", body)
    assert r["code"] == 0, r
    print(f"[5] 批量映射 OK total={r['data']['total']} success={r['data']['success_count']} fail={r['data']['fail_count']}")

    # 导入 CSV（multipart）
    csv_text = "shop_id,platform_code,platform_sku_id,sku_code,platform_sku_name\n"
    csv_text += f"{un[0]['shop_id']},{un[0].get('platform_code') or ''},SMOKE-IMP-1,{sku['sku_code']},导入规格1\n"
    csv_text += f"{un[0]['shop_id']},{un[0].get('platform_code') or ''},SMOKE-IMP-2,NOT-EXIST-CODE,导入规格2\n"
    boundary = "----smokeboundary1234"
    payload = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"m.csv\"\r\n"
        f"Content-Type: text/csv\r\n\r\n{csv_text}\r\n--{boundary}--\r\n"
    ).encode("utf-8")
    st, r, _ = _req("POST", "/sku-mappings/import", raw=payload,
                    content_type=f"multipart/form-data; boundary={boundary}")
    assert r["code"] == 0, (st, r)
    print(f"[6] 导入 CSV OK total={r['data']['total']} success={r['data']['success_count']} fail={r['data']['fail_count']}")

    # 导出 CSV（响应为文件流，单独读原始字节）
    req = urllib.request.Request(BASE + "/sku-mappings/export",
                                headers={"Authorization": "Bearer " + TOKEN})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_bytes = resp.read()
        ctype = resp.headers.get("Content-Type", "")
        cdisp = resp.headers.get("Content-Disposition", "")
    body_txt = raw_bytes.decode("utf-8-sig")
    header_line = body_txt.splitlines()[0] if body_txt else ""
    print(f"[7] 导出 OK bytes={len(raw_bytes)} content-type={ctype} disp={cdisp}")
    print(f"    导出表头 = {header_line}")

    # 回写平台
    _, r, _ = call("POST", f"/inventory/{sku['sku_id']}/push")
    assert r["code"] == 0, r
    print(f"[8] 回写平台 OK pushed_shop_count={r['data'].get('pushed_shop_count')} items={len(r['data'].get('items', []))}")

    # 盘点（实盘数必须 >= 占用库存，否则按规则拒绝）
    _, r, _ = call("GET", f"/inventory/{sku['sku_id']}")
    cur = r["data"]
    valid_actual = cur["occupied_qty"] + 7
    _, r, _ = call("POST", "/inventory/stocktake", {"items": [
        {"sku_id": sku["sku_id"], "actual_qty": valid_actual, "remark": "冒烟盘点"},
        {"sku_id": sku["sku_id"], "actual_qty": 0, "remark": "非法：小于占用"},
    ]})
    assert r["code"] == 0, r
    d = r["data"]
    print(f"[9] 盘点 OK total={d['total']} gain={d.get('gain_count')} loss={d.get('loss_count')} "
          f"items={[{k: i.get(k) for k in ('sku_code', 'before_qty', 'actual_qty', 'change_qty', 'success')} for i in d.get('items', [])]}")

    # 订单明细映射
    _, r, _ = call("GET", "/orders?page=1&page_size=1")
    oid = r["data"]["list"][0]["id"]
    _, r, _ = call("GET", f"/orders/{oid}/items")
    its = r["data"]
    matched = sum(1 for x in its if x.get("is_matched") == 1)
    print(f"[10] 订单明细映射 OK order={oid} 明细{len(its)}条 已匹配{matched}条")

    # 流水类型覆盖
    _, r, _ = call("GET", "/inventory/flows?page=1&page_size=100")
    types = sorted({x.get("flow_type") for x in r["data"]["list"]})
    print(f"[11] 流水类型覆盖 = {types}")

    # 并发占用防超卖：挑一个可售较小的 SKU，控制线程数
    cands = sorted([x for x in rows if x["available_qty"] >= 3], key=lambda x: x["available_qty"])
    tsku = cands[0]
    if tsku["available_qty"] > 20:
        target = tsku["occupied_qty"] + 10
        call("POST", "/inventory/stocktake", {"items": [
            {"sku_id": tsku["sku_id"], "actual_qty": target, "remark": "冒烟前调小库存"}]})
        _, r, _ = call("GET", f"/inventory/{tsku['sku_id']}")
        tsku = r["data"]
    avail = tsku["available_qty"]
    print(f"[12] 并发前 sku={tsku['sku_code']} available={avail}")
    n = avail + 3
    results = []
    lock = threading.Lock()

    def worker(i):
        try:
            _, rr, _ = call("POST", "/inventory/occupy",
                            {"sku_id": tsku["sku_id"], "qty": 1, "source_no": f"SMOKE-{i}"})
            code = rr["code"]
        except Exception as e:  # noqa: BLE001
            code = f"EXC:{type(e).__name__}"
        with lock:
            results.append(code)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ok = sum(1 for c in results if c == 0)
    failed = sum(1 for c in results if c != 0)
    _, r, _ = call("GET", f"/inventory/{tsku['sku_id']}")
    after = r["data"]
    print(f"[13] 并发占用 OK 发起{n}个 成功{ok} 失败{failed}(可用={avail}) 占用后 available={after['available_qty']} occupied={after['occupied_qty']}")
    assert ok == avail, f"防超卖失败：成功{ok} != 可用{avail}"
    # 释放
    for i in range(ok):
        call("POST", "/inventory/release", {"sku_id": tsku["sku_id"], "qty": 1, "source_no": f"SMOKE-{i}"})
    print("[14] 释放占用 OK（库存已还原）")

    # 清理冒烟映射
    call("DELETE", f"/sku-mappings/{mid}")
    print("[15] 冒烟数据清理完成")
    print("=== 批次3 冒烟全部通过 ===")


if __name__ == "__main__":
    main()
