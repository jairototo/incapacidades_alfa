import io, zipfile
import pytest


def _zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names:
            z.writestr(n, b"x")
    buf.seek(0); return buf


@pytest.mark.asyncio
async def test_zip_maps_filenames(client, empresa_user_token, test_empleado):
    doc = test_empleado.numero_documento
    buf = _zip([f"{doc}_INCAPACIDAD.pdf", f"{doc}_HISTORIA_CLINICA.jpg", "basura.txt"])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/zip",
        files={"archivo": ("docs.zip", buf, "application/zip")},
        data={"documentos_esperados": doc},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    matched = {(m["numero_documento"], m["tipo"]) for m in body["asignaciones"] if m["match"]}
    assert (doc, "INCAPACIDAD") in matched and (doc, "HISTORIA_CLINICA") in matched
    assert any(m["match"] is False for m in body["asignaciones"])  # basura.txt doesn't match convention


@pytest.mark.asyncio
async def test_corrupt_zip_returns_400(client, empresa_user_token):
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/zip",
        files={"archivo": ("fake.zip", io.BytesIO(b"%PDF not a zip"), "application/zip")},
        data={"documentos_esperados": "123"},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 400, resp.text
