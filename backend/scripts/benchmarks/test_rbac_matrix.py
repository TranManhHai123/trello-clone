"""
test_rbac_matrix.py — U4: Ma tran RBAC tu dong cho NHAN_XET.

Sinh bang N endpoint x 3 vai tro (owner / member / nguoi ngoai project),
so sanh ma HTTP ky vong voi ma HTTP thuc te. Dung pytest + requests, chay
truc tiep tren server dang song (giong test_ws_auth.py, measure_ws_latency.py)
thay vi TestClient + fixture DB rieng, vi du an chua co ha tang test DB.

CANH BAO: script tao du lieu that (user/project/task) qua API. Chay tren
DB dev/test, KHONG chay tren DB production.

Cach dung:
1. Backend dang chay o localhost:8000 (uvicorn app.main:app --reload)
2. pytest test_rbac_matrix.py -v -s
   Do do phu:  pytest test_rbac_matrix.py --cov=app --cov-report=term-missing
3. Bang markdown in ra cuoi phien chay -> dan thang vao Chuong 4.
   Moi endpoint la 1 test case rieng, nen FAIL se chi dung o dung endpoint/role.

Tu dang ky 3 tai khoan moi (owner/member/outsider) + 1 project moi moi lan
chay, KHONG dung du lieu san co trong DB -> ket qua tai lap doc lap voi
trang thai DB hien tai.

ROUTE da xac nhan tu members.py / projects.py that:
  - POST   /projects                              {name}                -> tao project
  - DELETE /projects/{project_id}                                        -> xoa project (204)
  - POST   /projects/{project_id}/members         {username, role}      -> moi thanh vien
    (member_service.add_member nhan USERNAME, khong phai user_id — khac voi
    mo ta cu trong tien_do_va_thay_doi.md muc #18, doc do da LOI THOI)
  - DELETE /projects/{project_id}/members/{user_id}                      -> xoa thanh vien (204)
  - GET    /projects/{project_id}/members                                -> ds thanh vien

VAN CON GIA DINH: khong con — da xac nhan qua member_service.py / project_service.py:
  - Moi username khong ton tai -> 404 (member_service.add_member, dong 29)
  - Xoa membership khong ton tai -> 404 (member_service.remove_member, dong 48-49)
  - Xoa project khong phai owner -> 403 (project_service.delete)
"""

import uuid
import requests
import pytest

BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "testpass123"


def _uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register(email, username, password) -> int:
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email, "username": username, "password": password,
    })
    assert res.status_code in (200, 201), f"Register failed for {email}: {res.text}"
    return res.json()["id"]


def _login(email, password) -> str:
    res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email, "password": password,
    })
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def ctx():
    """1 lan cho ca module: owner tao project, moi member vao, outsider dung ngoai."""
    suffix = uuid.uuid4().hex[:6]
    owner_username = f"owner_{suffix}"
    member_username = f"member_{suffix}"

    _register(f"owner_{suffix}@test.com", owner_username, PASSWORD)
    owner_token = _login(f"owner_{suffix}@test.com", PASSWORD)

    member_id = _register(f"member_{suffix}@test.com", member_username, PASSWORD)
    member_token = _login(f"member_{suffix}@test.com", PASSWORD)

    _register(f"outsider_{suffix}@test.com", f"outsider_{suffix}", PASSWORD)
    outsider_token = _login(f"outsider_{suffix}@test.com", PASSWORD)

    res = requests.post(f"{BASE_URL}/projects", json={"name": f"RBAC {suffix}"},
                         headers=_auth(owner_token))
    assert res.status_code in (200, 201), res.text
    project_id = res.json()["id"]

    # add_member nhan USERNAME (member_service.add_member(..., username, role))
    res = requests.post(f"{BASE_URL}/projects/{project_id}/members",
                         json={"username": member_username, "role": "member"},
                         headers=_auth(owner_token))
    assert res.status_code in (200, 201), f"Invite member failed: {res.text}"

    return {
        "project_id": project_id,
        "member_id": member_id,
        "tokens": {"owner": owner_token, "member": member_token, "outsider": outsider_token},
    }


def _new_task(ctx, title_prefix="task"):
    res = requests.post(f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
                         json={"title": _uniq(title_prefix)},
                         headers=_auth(ctx["tokens"]["owner"]))
    return res.json()["id"]


# ============ 11 ENDPOINT — moi ham nhan (ctx, token) -> Response ============

def ep_get_tasks(ctx, token):
    return requests.get(f"{BASE_URL}/projects/{ctx['project_id']}/tasks", headers=_auth(token))

def ep_create_task(ctx, token):
    return requests.post(f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
                          json={"title": _uniq("task")}, headers=_auth(token))

def ep_update_status(ctx, token):
    task_id = _new_task(ctx, "status_test")
    return requests.patch(f"{BASE_URL}/tasks/{task_id}",
                           json={"status": "in_progress"}, headers=_auth(token))

def ep_assign_task(ctx, token):
    task_id = _new_task(ctx, "assign_test")
    return requests.patch(f"{BASE_URL}/tasks/{task_id}",
                           json={"assigned_to": None}, headers=_auth(token))

def ep_delete_task(ctx, token):
    task_id = _new_task(ctx, "delete_test")
    return requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=_auth(token))

def ep_get_requests(ctx, token):
    return requests.get(f"{BASE_URL}/projects/{ctx['project_id']}/requests", headers=_auth(token))

def ep_resolve_request(ctx, token):
    task_id = _new_task(ctx, "resolve_test")
    req_res = requests.patch(f"{BASE_URL}/tasks/{task_id}",
                              json={"title": _uniq("pending")},
                              headers=_auth(ctx["tokens"]["member"]))
    request_id = req_res.json()["id"]
    return requests.patch(f"{BASE_URL}/projects/{ctx['project_id']}/requests/{request_id}",
                           json={"decision": "rejected"}, headers=_auth(token))

def ep_get_members(ctx, token):
    return requests.get(f"{BASE_URL}/projects/{ctx['project_id']}/members", headers=_auth(token))

def ep_invite_member(ctx, token):
    return requests.post(f"{BASE_URL}/projects/{ctx['project_id']}/members",
                          json={"username": _uniq("nonexistent"), "role": "member"},
                          headers=_auth(token))

def ep_remove_member(ctx, token):
    return requests.delete(f"{BASE_URL}/projects/{ctx['project_id']}/members/999999",
                            headers=_auth(token))

def ep_delete_project(ctx, token):
    # project moi hoan toan rieng cho tung lan goi -> khong dung project dung chung
    res = requests.post(f"{BASE_URL}/projects", json={"name": _uniq("throwaway")},
                         headers=_auth(ctx["tokens"]["owner"]))
    throwaway_id = res.json()["id"]
    return requests.delete(f"{BASE_URL}/projects/{throwaway_id}", headers=_auth(token))


# name -> (fn, {role: expected_status})
ENDPOINTS = {
    "GET /projects/{id}/tasks":            (ep_get_tasks,       {"owner": 200, "member": 200, "outsider": 403}),
    "POST /projects/{id}/tasks":           (ep_create_task,     {"owner": 200, "member": 200, "outsider": 403}),
    "PATCH /tasks/{id} (status)":          (ep_update_status,   {"owner": 200, "member": 200, "outsider": 403}),
    "PATCH /tasks/{id} (assigned_to)":     (ep_assign_task,     {"owner": 200, "member": 403, "outsider": 403}),
    "DELETE /tasks/{id}":                  (ep_delete_task,     {"owner": 200, "member": 200, "outsider": 403}),
    "GET /projects/{id}/requests":         (ep_get_requests,    {"owner": 200, "member": 200, "outsider": 403}),
    "PATCH /projects/{id}/requests/{rid}": (ep_resolve_request, {"owner": 200, "member": 403, "outsider": 403}),
    "GET /projects/{id}/members":          (ep_get_members,     {"owner": 200, "member": 200, "outsider": 403}),
    "POST /projects/{id}/members":         (ep_invite_member,   {"owner": 404, "member": 403, "outsider": 403}),  # xac nhan tu member_service.py dong 29
    "DELETE /projects/{id}/members/{uid}": (ep_remove_member,   {"owner": 404, "member": 403, "outsider": 403}),  # xac nhan tu member_service.py dong 48-49
    "DELETE /projects/{id}":               (ep_delete_project,  {"owner": 204, "member": 403, "outsider": 403}),  # xac nhan tu @router.delete(status_code=204)
}

RESULTS = []  # (endpoint_name, {role: actual}, {role: expected})


@pytest.mark.parametrize("name", ENDPOINTS.keys())
def test_rbac_matrix(ctx, name):
    fn, expected = ENDPOINTS[name]
    actual = {}
    failures = []

    for role in ("owner", "member", "outsider"):
        token = ctx["tokens"][role]
        try:
            res = fn(ctx, token)
            actual[role] = res.status_code
        except Exception as e:
            actual[role] = f"ERROR:{e}"
        if actual[role] != expected[role]:
            failures.append(f"{role}: expected {expected[role]}, got {actual[role]}")

    RESULTS.append((name, actual, expected))

    if failures:
        pytest.fail(f"{name} -> " + "; ".join(failures))


def test_cancel_request_ignores_project_membership(ctx):
    """
    Endpoint DELETE .../requests/{id} (cancel) tung KHONG kiem tra
    project_member_repo.is_member() truoc khi cho phep huy — chi kiem tra
    request.requester_id == user_id. Da vao vao task_request_service.cancel()
    them dong is_member() check. Test nay CHUNG MINH fix con hieu luc: owner
    xoa member khoi project, roi member (da bi xoa) thu cancel request cu cua
    chinh minh -> phai bi tu choi 403. Neu regression tai xuat hien (cancel
    lai tra ve 200), test nay FAIL ngay.
    """
    task_id = _new_task(ctx, "cancel_gap_test")
    req_res = requests.patch(f"{BASE_URL}/tasks/{task_id}",
                              json={"title": _uniq("pending")},
                              headers=_auth(ctx["tokens"]["member"]))
    request_id = req_res.json()["id"]

    # owner xoa member khoi project NGAY BAY GIO -> member khong con la
    # thanh vien nua, nhung JWT cua ho van con hieu luc (token khong bi thu hoi).
    remove_res = requests.delete(
        f"{BASE_URL}/projects/{ctx['project_id']}/members/{ctx['member_id']}",
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert remove_res.status_code == 204, f"Remove member that bai: {remove_res.text}"

    # member (da bi xoa khoi project) van thu cancel request cu cua chinh minh
    cancel_res = requests.delete(
        f"{BASE_URL}/projects/{ctx['project_id']}/requests/{request_id}",
        headers=_auth(ctx["tokens"]["member"]),
    )

    gap_closed = cancel_res.status_code == 403

    RESULTS.append((
        "DELETE requests/{rid} (cancel sau khi bi xoa khoi project)",
        {"member(da bi remove)": cancel_res.status_code},
        {"member(da bi remove)": 403},
    ))

    if not gap_closed:
        print(
            "\n[GAP VAN CON] Member da bi xoa khoi project van cancel duoc "
            f"request_id={request_id} -> HTTP {cancel_res.status_code} "
            "(ky vong 403). task_request_service.cancel() thieu is_member() check."
        )

    assert gap_closed, (
        f"Member da bi remove khoi project van cancel duoc request (HTTP {cancel_res.status_code}, "
        "ky vong 403) -> them project_member_repo.is_member() check vao cancel()."
    )
def test_create_request_approve_flow(ctx):
    """
    Member tao task -> pending TaskRequest (action_type=create). Owner approve ->
    xac nhan task THAT SU duoc persist: xuat hien trong GET /projects/{id}/tasks
    voi dung title da gui, va request bien mat khoi danh sach pending.
    Phu trach nhanh _execute() cho RequestAction.create trong task_request_service.py.
    """
    title = _uniq("create_approve_flow")
    create_res = requests.post(
        f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
        json={"title": title},
        headers=_auth(ctx["tokens"]["member"]),
    )
    assert create_res.status_code in (200, 201), create_res.text
    body = create_res.json()
    assert "action_type" in body, f"Member create phai tra ve TaskRequest, got: {body}"
    request_id = body["id"]

    resolve_res = requests.patch(
        f"{BASE_URL}/projects/{ctx['project_id']}/requests/{request_id}",
        json={"decision": "approved"},
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert resolve_res.status_code == 200, resolve_res.text
    assert resolve_res.json()["status"] == "approved"

    tasks_res = requests.get(
        f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
        headers=_auth(ctx["tokens"]["owner"]),
    )
    titles = [t["title"] for t in tasks_res.json()]
    assert title in titles, f"Task '{title}' khong xuat hien sau khi approve"

    pending_res = requests.get(
        f"{BASE_URL}/projects/{ctx['project_id']}/requests",
        headers=_auth(ctx["tokens"]["owner"]),
    )
    pending_ids = [r["id"] for r in pending_res.json()]
    assert request_id not in pending_ids, "Request van con pending sau khi da approve"


def test_update_request_reject_flow(ctx):
    """
    Member sua title task -> pending TaskRequest (action_type=update). Owner reject ->
    xac nhan task title KHONG doi (van la title cu). Phu trach nhanh reject
    (bo qua _execute) trong task_request_service.py.
    """
    task_id = _new_task(ctx, "update_reject_flow")
    tasks_before = requests.get(
        f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
        headers=_auth(ctx["tokens"]["owner"]),
    ).json()
    original_title = next(t["title"] for t in tasks_before if t["id"] == task_id)

    new_title = _uniq("rejected_title")
    update_res = requests.patch(
        f"{BASE_URL}/tasks/{task_id}",
        json={"title": new_title},
        headers=_auth(ctx["tokens"]["member"]),
    )
    assert update_res.status_code == 200, update_res.text
    body = update_res.json()
    assert "action_type" in body, f"Member update phai tra ve TaskRequest, got: {body}"
    request_id = body["id"]

    resolve_res = requests.patch(
        f"{BASE_URL}/projects/{ctx['project_id']}/requests/{request_id}",
        json={"decision": "rejected"},
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert resolve_res.status_code == 200, resolve_res.text
    assert resolve_res.json()["status"] == "rejected"

    tasks_after = requests.get(
        f"{BASE_URL}/projects/{ctx['project_id']}/tasks",
        headers=_auth(ctx["tokens"]["owner"]),
    ).json()
    current_title = next(t["title"] for t in tasks_after if t["id"] == task_id)
    assert current_title == original_title, (
        f"Task title bi doi mac du request da reject: '{original_title}' -> '{current_title}'"
    )


def test_project_update_delete_rbac(ctx):
    """
    project_service.update() va delete(): owner thanh cong, member bi 403.
    Dung project RIENG de khong anh huong ctx['project_id'] dung chung.
    """
    create_res = requests.post(
        f"{BASE_URL}/projects",
        json={"name": _uniq("update_delete_test")},
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert create_res.status_code in (200, 201), create_res.text
    project_id = create_res.json()["id"]

    member_update_res = requests.patch(
        f"{BASE_URL}/projects/{project_id}",
        json={"name": _uniq("member_should_fail")},
        headers=_auth(ctx["tokens"]["member"]),
    )
    assert member_update_res.status_code == 403, member_update_res.text

    owner_new_name = _uniq("owner_updated")
    owner_update_res = requests.patch(
        f"{BASE_URL}/projects/{project_id}",
        json={"name": owner_new_name},
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert owner_update_res.status_code == 200, owner_update_res.text
    assert owner_update_res.json()["name"] == owner_new_name

    member_delete_res = requests.delete(
        f"{BASE_URL}/projects/{project_id}",
        headers=_auth(ctx["tokens"]["member"]),
    )
    assert member_delete_res.status_code == 403, member_delete_res.text

    owner_delete_res = requests.delete(
        f"{BASE_URL}/projects/{project_id}",
        headers=_auth(ctx["tokens"]["owner"]),
    )
    assert owner_delete_res.status_code == 204, owner_delete_res.text


def _print_markdown_table():
    print("\n\n=== BANG MA TRAN RBAC (dan vao Chuong 4) ===\n")
    print("| Endpoint | Owner (kỳ vọng/thực tế) | Member | Outsider |")
    print("|---|---|---|---|")
    ok, total = 0, 0
    for name, actual, expected in RESULTS:
        cells = []
        for role in expected.keys():
            e, a = expected[role], actual[role]
            match = (str(e).split()[0] == str(a)) if isinstance(e, str) else (e == a)
            if isinstance(e, int):
                total += 1
                ok += int(match)
            mark = "✅" if match else "❌"
            cells.append(f"{e}/{a} {mark}")
        row = " | ".join(cells)
        print(f"| {name} | {row} |")
    print(f"\nTong: {ok}/{total} o dung ky vong (khong tinh dong ghi-nhan-gap).")


@pytest.fixture(scope="module", autouse=True)
def _print_summary(request):
    yield
    _print_markdown_table()