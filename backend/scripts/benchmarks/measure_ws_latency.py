"""
measure_ws_latency.py — Do do tre lan truyen WebSocket broadcast cho U2 (NHAN_XET Muc 4).

Muc dich: Voi N client dang lang nghe WebSocket tren cung 1 project, do thoi gian
tu luc mot HTTP PATCH duoc gui di (doi status cua 1 task) den luc TUNG client
WebSocket nhan duoc su kien TASK_UPDATED tuong ung. Lap 200 lan cho moi muc
N trong {2, 5, 10, 25, 50}, bo qua 20 lan dau (lam nong).

Cach dung:
1. Dam bao backend dang chay o localhost:8000
     pip install websockets requests --break-system-packages
   Chay:
     python measure_ws_latency.py
5. Ket qua:
   - In ra man hinh bang tom tat p50/p95/p99 (ms) theo tung muc N.
   - Ghi du lieu tho ra ws_latency_raw.csv (moi dong = 1 lan 1 client nhan event)
     de sau nay ve bieu do that trong Chuong 4 (truc X = N, truc Y = do tre,
     3 duong p50/p95/p99).

"""

import asyncio
import csv
import platform
import statistics
import time
from dataclasses import dataclass, field

import requests
import websockets

# ============ DIEN THONG TIN THAT CUA BAN VAO DAY ============
# QUAN TRONG (Windows): dung 127.0.0.1, KHONG dung "localhost". Tren nhieu may Windows,
# resolve "localhost" qua requests/websockets bi treo ~2 giay moi lan do getaddrinfo()
# uu tien IPv6 truoc roi moi fallback IPv4. 127.0.0.1 bo qua buoc resolve nay hoan toan.
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
LOGIN = {"email": "user2@example.com", "password": "user2"}  
PROJECT_ID = 4          
# ================================================================

N_LEVELS = [2, 5, 10, 25, 50]
ITERATIONS_PER_LEVEL = 200
WARMUP_ITERATIONS = 20
PER_MESSAGE_TIMEOUT = 5.0  # giay, neu qua thoi gian nay ma client chua nhan duoc -> coi la mat goi
OUTPUT_CSV = "ws_latency_raw.csv"


@dataclass
class ClientListener:
    """Mot ket noi WebSocket lang nghe, day timestamp nhan duoc vao queue rieng."""
    index: int
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    _task: asyncio.Task | None = None
    _ws: object = None

    async def start(self, token: str):
        url = f"{WS_URL}/ws/projects/{PROJECT_ID}?token={token}"
        self._ws = await websockets.connect(url, open_timeout=10)
        self._task = asyncio.create_task(self._reader())

    async def _reader(self):
        try:
            async for raw in self._ws:
                recv_time = time.perf_counter()
                await self.queue.put((recv_time, raw))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def close(self):
        if self._task:
            self._task.cancel()
        if self._ws:
            await self._ws.close()


def login(creds: dict) -> str:
    print(f"[login] Dang login voi {creds['email']} ...", flush=True)
    data = {"username": creds["email"], "password": creds["password"]}
    try:
        res = requests.post(f"{BASE_URL}/auth/login", data=data, timeout=5)
    except requests.exceptions.ConnectionError:
        raise SystemExit(
            f"[login] KHONG KET NOI DUOC toi {BASE_URL}. "
            "Kiem tra uvicorn co dang chay khong."
        )
    if res.status_code != 200:
        raise SystemExit(f"[login] That bai ({res.status_code}): {res.text}")
    print("[login] OK", flush=True)
    return res.json()["access_token"]


async def toggle_status_patch(session: requests.Session, token: str, current_status: str) -> tuple[float, str]:
    """Gui PATCH doi status task, chay trong thread executor de khong block event loop.
    Dung chung 1 requests.Session de tai su dung ket noi TCP (keep-alive) thay vi
    mo ket noi moi moi lan goi - tranh cong them chi phi TCP handshake vao moi mau do.
    Tra ve (t_send, new_status)."""
    new_status = "in_progress" if current_status == "todo" else "todo"

    def _do_patch():
        return session.patch(
            f"{BASE_URL}/tasks/{TASK_ID}",
            json={"status": new_status},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

    loop = asyncio.get_event_loop()
    t_send = time.perf_counter()
    res = await loop.run_in_executor(None, _do_patch)
    if res.status_code != 200:
        raise RuntimeError(
            f"PATCH that bai ({res.status_code}): {res.text}. "
            "Kiem tra TASK_ID co ton tai va thuoc PROJECT_ID, va tai khoan co quyen sua."
        )
    return t_send, new_status


async def run_level(n: int, token: str, session: requests.Session, csv_writer) -> dict:
    print(f"\n=== N = {n} client ===", flush=True)
    clients = [ClientListener(index=i) for i in range(n)]
    # Mo tat ca N ket noi CUNG LUC (concurrent), khong tuan tu, de tranh cong don
    # do tre setup ket noi qua tung client mot khi N lon.
    await asyncio.gather(*(c.start(token) for c in clients))
    # cho cac ket noi on dinh truoc khi bat dau do
    await asyncio.sleep(0.3)

    current_status = "todo"
    all_latencies_ms: list[float] = []

    total_iterations = WARMUP_ITERATIONS + ITERATIONS_PER_LEVEL
    for it in range(total_iterations):
        is_warmup = it < WARMUP_ITERATIONS
        t_send, current_status = await toggle_status_patch(session, token, current_status)

        for c in clients:
            try:
                recv_time, _raw = await asyncio.wait_for(c.queue.get(), timeout=PER_MESSAGE_TIMEOUT)
            except asyncio.TimeoutError:
                print(f"  [!] Client {c.index} khong nhan duoc event o iteration {it} (bo qua)")
                continue
            latency_ms = (recv_time - t_send) * 1000
            if not is_warmup:
                all_latencies_ms.append(latency_ms)
                csv_writer.writerow([n, it - WARMUP_ITERATIONS, c.index, f"{latency_ms:.3f}"])

        if (it + 1) % 50 == 0:
            tag = "warmup" if is_warmup else "do"
            print(f"  ...{it + 1}/{total_iterations} iterations ({tag})", flush=True)

    for c in clients:
        await c.close()

    summary = {
        "n": n,
        "count": len(all_latencies_ms),
        "p50": percentile(all_latencies_ms, 50),
        "p95": percentile(all_latencies_ms, 95),
        "p99": percentile(all_latencies_ms, 99),
        "mean": statistics.mean(all_latencies_ms) if all_latencies_ms else float("nan"),
    }
    print(
        f"  N={n}: p50={summary['p50']:.2f}ms  p95={summary['p95']:.2f}ms  "
        f"p99={summary['p99']:.2f}ms  (mean={summary['mean']:.2f}ms, n_samples={summary['count']})"
    )
    return summary


def percentile(data: list[float], p: int) -> float:
    if not data:
        return float("nan")
    if len(data) == 1:
        return data[0]
    cut_points = statistics.quantiles(data, n=100, method="inclusive")
    return cut_points[p - 1]


async def main():
    print("[main] Bat dau do do tre WebSocket broadcast (U2)...", flush=True)
    print(f"[main] Cau hinh may: {platform.platform()}, CPU count = {__import__('os').cpu_count()}")
    token = login(LOGIN)
    session = requests.Session()

    summaries = []
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n_clients", "iteration", "client_index", "latency_ms"])
        for n in N_LEVELS:
            summary = await run_level(n, token, session, writer)
            summaries.append(summary)
    session.close()

    print("\n=== TOM TAT (dan vao Chuong 4) ===")
    print(f"{'N':<6}{'p50 (ms)':<12}{'p95 (ms)':<12}{'p99 (ms)':<12}{'mean (ms)':<12}{'samples':<10}")
    for s in summaries:
        print(
            f"{s['n']:<6}{s['p50']:<12.2f}{s['p95']:<12.2f}{s['p99']:<12.2f}"
            f"{s['mean']:<12.2f}{s['count']:<10}"
        )
    print(f"\nDu lieu tho da ghi vao {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())