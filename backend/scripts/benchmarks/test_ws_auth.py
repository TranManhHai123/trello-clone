"""
test_ws_auth.py — Kiem chung 4 kich ban xac thuc WebSocket cho U1.

Cach dung:
1. Dam bao backend dang chay o localhost:8000 (uvicorn app.main:app --reload)
2. Can 2 tai khoan da co san trong DB:
   - USER_A: la member cua PROJECT_ID (dung de lay VALID_TOKEN)
   - USER_B: KHONG phai member cua PROJECT_ID (dung de lay OUTSIDER_TOKEN)
3. Dien 3 bien duoi day bang du lieu that cua ban roi chay:
     pip install websockets requests --break-system-packages
     python test_ws_auth.py

Chay 2 LAN:
  - Lan 1: voi code GOC (chua vá, khong co token/is_member check) -> ghi lai cot "Truoc"
  - Lan 2: voi code DA VA (hien tai trong tasks.py) -> ghi lai cot "Sau"
"""

import asyncio
import requests
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
PROJECT_ID = 4          # project ma USER_A la member, USER_B khong phai
VALID_LOGIN = {"email": "user1@example.com", "password": "user1"}
OUTSIDER_LOGIN = {"email": "user5@example.com", "password": "user5"}


def login(creds: dict) -> str:
    print(f"[login] Dang login voi {creds['email']} ...", flush=True)
    data = {"username": creds["email"], "password": creds["password"]}
    try:
        res = requests.post(f"{BASE_URL}/auth/login", data=data, timeout=5)
    except requests.exceptions.ConnectionError:
        raise SystemExit(
            f"[login] KHONG KET NOI DUOC toi {BASE_URL}. "
            "Kiem tra uvicorn co dang chay khong (mo http://localhost:8000/docs xem co load duoc)."
        )
    except requests.exceptions.Timeout:
        raise SystemExit(f"[login] Timeout khi goi {BASE_URL}/auth/login")
    if res.status_code != 200:
        raise SystemExit(
            f"[login] That bai ({res.status_code}): {res.text}\n"
            f"-> Kiem tra lai email/password trong VALID_LOGIN / OUTSIDER_LOGIN da dung chua."
        )
    print(f"[login] OK, lay duoc token cho {creds['email']}", flush=True)
    return res.json()["access_token"]


async def try_connect(url: str, label: str) -> dict:
    """Tra ve dict {label, connected, close_code, received_message}"""
    print(f"[ws] Dang thu ket noi: {label} ...", flush=True)
    try:
        async with websockets.connect(url, open_timeout=5) as ws:
            # Neu connect duoc, cho toi da 2s xem co nhan duoc broadcast khong
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                received = True
            except asyncio.TimeoutError:
                received = False
            return {
                "label": label,
                "connected": True,
                "close_code": None,
                "received_message": received,
            }
    except websockets.exceptions.InvalidStatusCode as e:
        return {"label": label, "connected": False, "close_code": e.status_code, "received_message": False}
    except websockets.exceptions.ConnectionClosedError as e:
        return {"label": label, "connected": False, "close_code": e.code, "received_message": False}
    except Exception as e:
        return {"label": label, "connected": False, "close_code": f"ERROR:{e}", "received_message": False}


async def main():
    print("[main] Bat dau...", flush=True)
    valid_token = login(VALID_LOGIN)
    outsider_token = login(OUTSIDER_LOGIN)
    print("[main] Da co ca 2 token, bat dau test WebSocket...", flush=True)

    scenarios = [
        ("Khong token", f"{WS_URL}/ws/projects/{PROJECT_ID}"),
        ("Token sai chu ky", f"{WS_URL}/ws/projects/{PROJECT_ID}?token=eyJinvalid.fake.token"),
        ("Token hop le, KHONG phai member", f"{WS_URL}/ws/projects/{PROJECT_ID}?token={outsider_token}"),
        ("Token hop le, LA member", f"{WS_URL}/ws/projects/{PROJECT_ID}?token={valid_token}"),
    ]

    print(f"{'Kich ban':<40} | {'Ket noi?':<10} | {'Ma dong':<10}")
    print("-" * 65)
    results = []
    for label, url in scenarios:
        r = await try_connect(url, label)
        results.append(r)
        conn_str = "Co" if r["connected"] else "Khong"
        print(f"{r['label']:<40} | {conn_str:<10} | {str(r['close_code']):<10}")

    return results


if __name__ == "__main__":
    asyncio.run(main())