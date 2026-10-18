"""API tests using a temporary SQLite database (no MySQL connection required)."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Load the real FastAPI app with an isolated temporary database engine."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'job_hunting_test.db'}",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """))
        connection.execute(text("""
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                application_status TEXT NOT NULL,
                applied_date DATE,
                job_url TEXT,
                notes TEXT,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """))

    # main.py imports `engine` from database.py. Replace this dependency BEFORE
    # loading main.py so tests cannot use the developer's real MySQL database.
    database_stub = types.ModuleType("database")
    database_stub.engine = engine
    monkeypatch.setitem(sys.modules, "database", database_stub)

    project_root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("job_hunting_main_under_test", project_root / "main.py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    with TestClient(app_module.app) as test_client:
        yield test_client
    engine.dispose()


def add_company(client, name="テスト株式会社", company_type="IT"):
    response = client.post("/companies", json={"name": name, "type": company_type})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def add_application(client, company_id, **overrides):
    data = {
        "company_id": company_id,
        "position": "Pythonエンジニア",
        "application_status": "書類選考",
        "notes": "テスト応募",
    }
    data.update(overrides)
    response = client.post("/applications", json=data)
    assert response.status_code == 200, response.text
    return response


def test_home(client):
    assert client.get("/").json()["message"] == "求职管理系统"


def test_company_crud(client):
    company_id = add_company(client)
    assert client.get(f"/companies/{company_id}").json()["name"] == "テスト株式会社"
    assert any(row["id"] == company_id for row in client.get("/companies").json())

    updated = client.put(
        f"/companies/{company_id}",
        json={"name": "更新後株式会社", "type": "メーカー"},
    )
    assert updated.status_code == 200
    assert client.get(f"/companies/{company_id}").json()["type"] == "メーカー"

    assert client.delete(f"/companies/{company_id}").status_code == 200
    assert client.get(f"/companies/{company_id}").status_code == 404


@pytest.mark.parametrize("path, method, payload", [
    ("/companies/9999", "get", None),
    ("/companies/9999", "put", {"name": "会社", "type": "IT"}),
    ("/companies/9999", "delete", None),
])
def test_missing_company_returns_404(client, path, method, payload):
    response = getattr(client, method)(path, **({"json": payload} if payload else {}))
    assert response.status_code == 404


def test_company_search(client):
    add_company(client, "東京IT", "開発")
    add_company(client, "大阪工業", "製造")
    response = client.get("/companies/search", params={"keyword": "IT"})
    assert response.status_code == 200
    assert [row["name"] for row in response.json()["companies"]] == ["東京IT"]


def test_empty_company_search_returns_empty_list(client):
    response = client.get("/companies/search", params={"keyword": " "})
    assert response.status_code == 200
    assert response.json()["companies"] == []


@pytest.mark.parametrize("payload", [
    {"name": "", "type": "IT"},
    {"name": "    ", "type": "IT"},
    {"name": "会社", "type": "\t"},
    {"name": "会社", "type": ""},
])
def test_reject_blank_company_information(client, payload):
    assert client.post("/companies", json=payload).status_code == 422


def test_reject_blank_company_information_on_update(client):
    company_id = add_company(client)
    response = client.put(
        f"/companies/{company_id}", json={"name": "  ", "type": "IT"}
    )
    assert response.status_code == 422
    assert client.get(f"/companies/{company_id}").json()["name"] == "テスト株式会社"


def test_trim_company_information(client):
    company_id = add_company(client, "  テスト商事  ", "  IT  ")
    company = client.get(f"/companies/{company_id}").json()
    assert company["name"] == "テスト商事"
    assert company["type"] == "IT"


def test_application_create_and_get_by_id(client):
    company_id = add_company(client)
    response = add_application(client, company_id)
    assert response.json()["position"] == "Pythonエンジニア"
    listing = client.get("/applications").json()["applications"]
    assert len(listing) == 1
    application_id = listing[0]["id"]
    detail = client.get(f"/applications/{application_id}")
    assert detail.status_code == 200
    assert detail.json()["company_name"] == "テスト株式会社"
    assert detail.json()["position"] == "Pythonエンジニア"


def test_application_update(client):
    company_id = add_company(client)
    add_application(client, company_id)
    app_id = client.get("/applications").json()["applications"][0]["id"]
    response = client.put(f"/applications/{app_id}", json={
        "company_id": company_id,
        "position": "Javaエンジニア",
        "application_status": "一次面接",
    })
    assert response.status_code == 200
    detail = client.get(f"/applications/{app_id}").json()
    assert detail["position"] == "Javaエンジニア"
    assert detail["application_status"] == "一次面接"


def test_application_delete(client):
    company_id = add_company(client)
    add_application(client, company_id)
    app_id = client.get("/applications").json()["applications"][0]["id"]
    assert client.delete(f"/applications/{app_id}").status_code == 200
    assert client.get(f"/applications/{app_id}").status_code == 404


@pytest.mark.parametrize("method, path, payload", [
    ("get", "/applications/9999", None),
    ("put", "/applications/9999", {"company_id": 1, "position": "SE", "application_status": "応募済"}),
    ("delete", "/applications/9999", None),
])
def test_missing_application_returns_404(client, method, path, payload):
    response = getattr(client, method)(path, **({"json": payload} if payload else {}))
    assert response.status_code == 404


@pytest.mark.parametrize("payload", [
    {"company_id": 1, "position": "", "application_status": "応募済"},
    {"company_id": 1, "position": "  ", "application_status": "応募済"},
    {"company_id": 1, "position": "SE", "application_status": "   "},
    {"company_id": 0, "position": "SE", "application_status": "応募済"},
    {"company_id": -1, "position": "SE", "application_status": "応募済"},
])
def test_application_input_validation_returns_422(client, payload):
    assert client.post("/applications", json=payload).status_code == 422


def test_application_update_input_validation(client):
    company_id = add_company(client)
    add_application(client, company_id)
    app_id = client.get("/applications").json()["applications"][0]["id"]
    response = client.put(f"/applications/{app_id}", json={
        "company_id": company_id,
        "position": " ",
        "application_status": "応募済",
    })
    assert response.status_code == 422
    assert client.get(f"/applications/{app_id}").json()["position"] == "Pythonエンジニア"


def test_application_unknown_company_returns_404(client):
    response = client.post("/applications", json={
        "company_id": 9999, "position": "SE", "application_status": "応募済"
    })
    assert response.status_code == 404


def test_application_update_unknown_company_returns_404(client):
    company_id = add_company(client)
    add_application(client, company_id)
    app_id = client.get("/applications").json()["applications"][0]["id"]
    response = client.put(f"/applications/{app_id}", json={
        "company_id": 9999, "position": "SE", "application_status": "応募済"
    })
    assert response.status_code == 404


def test_application_multi_keyword_search(client):
    company_id = add_company(client, "東京開発株式会社")
    add_application(client, company_id, position="Pythonエンジニア", application_status="一次面接")
    add_application(client, company_id, position="営業", application_status="一次面接")
    response = client.get("/applications", params={"keyword": "Python 一次面接"})
    assert response.status_code == 200
    rows = response.json()["applications"]
    assert len(rows) == 1
    assert rows[0]["position"] == "Pythonエンジニア"


def test_old_singular_application_url_is_not_registered(client):
    assert client.get("/application/1").status_code == 404
