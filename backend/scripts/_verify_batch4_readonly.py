"""批次4 前端联调只读探针（临时验证用，用户可自行删除）。

只做 GET 请求，验证 8000 端口后端暴露了前端批次4页面依赖的全部读接口契约。
BASE 可用环境变量 OH_BASE 覆盖，默认 http://127.0.0.1:8000/api/v1
"""
import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("OH_BASE", "http://127.0.0.1:8000/api/v1")
TOKEN = ""

FAIL = []


def req(method, path):
    hdrs = {"Authorization": "Bearer " + TOKEN} if TOKEN else {}
    r = urllib.request.Request(BASE + path, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def check(name, method, path, want_data=True):
    st, r = req(method, path)
    ok = st == 200 and r.get("code") == 0
    if want_data and ok:
        ok = r.get("data") is not None
    data = r.get("data")
    # 取一条样本 id 方便后续 detail 探测
    sample_id = None
    if isinstance(data, dict) and isinstance(data.get("list"), list) and data["list"]:
        sample_id = data["list"][0].get("id")
    elif isinstance(data, list) and data:
        sample_id = data[0].get("id")
    flag = "OK " if ok else "FAIL"
    print(f"[{flag}] {name:32s} {method} {path} -> code={r.get('code')} msg={r.get('message')}")
    if not ok:
        FAIL.append(name)
    return sample_id


def main():
    global TOKEN
    body = json.dumps({"username": "admin", "password": "123456"}).encode("utf-8")
    rq = urllib.request.Request(
        BASE + "/auth/login", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(rq, timeout=30) as resp:
        r = json.loads(resp.read().decode("utf-8"))
    assert r["code"] == 0, r
    TOKEN = r["data"]["token"]
    print("[OK ] 登录 admin/123456")

    # ---------------- M3 订单处理 ---------------- #
    oid = check("异常订单池", "GET", "/orders/abnormal?page=1&page_size=10")
    oid = oid or check("订单列表", "GET", "/orders?page=1&page_size=10")
    check("订单状态可选项", "GET", f"/orders/{oid}/status-options")
    check("订单详情", "GET", f"/orders/{oid}")
    check("订单商品明细", "GET", f"/orders/{oid}/items")
    check("订单日志变更", "GET", f"/orders/{oid}/logs")
    check("订单关联售后", "GET", f"/orders/{oid}/after-sales")

    # ---------------- M6 发货与物流 ---------------- #
    check("物流公司字典", "GET", "/logistics-companies")
    check("待发货列表", "GET", "/shipments/pending?page=1&page_size=10")
    check("发货记录列表", "GET", "/shipments?page=1&page_size=10")
    check("物流异常预警", "GET", "/shipments/alerts?page=1&page_size=10")
    sdetail = None
    st, r = req("GET", "/shipments?page=1&page_size=10")
    if r.get("code") == 0 and r["data"]["list"]:
        sdetail = r["data"]["list"][0]["id"]
    if sdetail:
        check("发货单详情", "GET", f"/shipments/{sdetail}")
        check("物流轨迹", "GET", f"/shipments/{sdetail}/traces")

    # ---------------- M7 售后管理 ---------------- #
    check("售后单列表", "GET", "/after-sales?page=1&page_size=10")
    check("售后超时预警", "GET", "/after-sales/alerts?page=1&page_size=10")
    check("售后原因分析", "GET", "/after-sales/analysis")
    aid = None
    st, r = req("GET", "/after-sales?page=1&page_size=10")
    if r.get("code") == 0 and r["data"]["list"]:
        aid = r["data"]["list"][0]["id"]
    if aid:
        check("售后单详情", "GET", f"/after-sales/{aid}")

    print(f"\n==== 只读探针完成：失败 {len(FAIL)} 项 ====")
    if FAIL:
        print("失败项：", FAIL)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
