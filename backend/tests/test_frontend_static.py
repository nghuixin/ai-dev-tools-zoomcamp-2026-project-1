from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_frontend


def test_backend_serves_frontend_without_shadowing_api(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Site Issue Triage</title>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("export default 1")
    (tmp_path / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

    application = FastAPI()

    @application.get("/api/studies")
    def list_studies():
        return [{"id": 1, "code": "ST-104", "name": "HARMONY NSCLC"}]

    assert mount_frontend(application, tmp_path) is True
    client = TestClient(application)

    home = client.get("/")
    assert home.status_code == 200
    assert "Site Issue Triage" in home.text
    log = client.get("/log")
    assert log.status_code == 200
    assert "Site Issue Triage" in log.text
    assert client.get("/assets/app.js").text == "export default 1"
    assert client.get("/favicon.svg").status_code == 200
    assert client.get("/api/studies").json() == [
        {"id": 1, "code": "ST-104", "name": "HARMONY NSCLC"}
    ]


def test_mount_skipped_when_frontend_is_missing(tmp_path):
    application = FastAPI()
    assert mount_frontend(application, tmp_path) is False
    assert TestClient(application).get("/").status_code == 404
