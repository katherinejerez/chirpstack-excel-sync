"""
Script de PRUEBA v2 — habla gRPC-Web directamente (el mismo protocolo que usa
el navegador para mostrar la interfaz de ChirpStack), en vez de gRPC nativo,
que ya confirmamos que el servidor rechaza en el puerto público.

Cómo usarlo (en GitHub Actions, vía el workflow test-chirpstack.yml):
- Solo reemplaza este archivo en tu repo (mismo nombre) y vuelve a correr
  el workflow "Run workflow". Usa el secreto CHIRPSTACK_API_TOKEN que ya
  configuraste.
"""

import os
import struct
import requests
from chirpstack_api import api

HOST = "chirpstack-cyt.tecnoandina.cl"
TENANT_ID = "7326cdb4-b1b2-4b35-ad5a-a5051f9c05e5"
API_TOKEN = os.environ.get("CHIRPSTACK_API_TOKEN", "PON_TU_TOKEN_AQUI")


def _frame(payload: bytes) -> bytes:
    """Empaqueta un mensaje protobuf en el formato de frame de gRPC-Web:
    1 byte de flag (0 = sin comprimir) + 4 bytes de largo (big-endian) + payload.
    """
    return struct.pack(">BI", 0, len(payload)) + payload


def _parse_frames(body: bytes):
    frames = []
    i = 0
    while i < len(body):
        if i + 5 > len(body):
            break
        flag = body[i]
        length = struct.unpack(">I", body[i + 1:i + 5])[0]
        payload = body[i + 5:i + 5 + length]
        frames.append((flag, payload))
        i += 5 + length
    return frames


def grpc_web_call(service: str, method: str, request_message, response_cls, timeout=15):
    url = f"https://{HOST}/{service}/{method}"
    body = _frame(request_message.SerializeToString())
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "Accept": "application/grpc-web+proto",
        "X-Grpc-Web": "1",
        "Authorization": f"Bearer {API_TOKEN}",
    }

    resp = requests.post(url, data=body, headers=headers, timeout=timeout)

    print(f"  -> HTTP {resp.status_code}, content-type: {resp.headers.get('content-type')}")

    if resp.status_code != 200:
        print(f"  -> Cuerpo de la respuesta (primeros 500 caracteres):\n{resp.text[:500]}")
        resp.raise_for_status()

    frames = _parse_frames(resp.content)
    message_payload = None
    trailer_payload = None
    for flag, payload in frames:
        if flag & 0x80:
            trailer_payload = payload
        else:
            message_payload = payload

    trailers = {}
    if trailer_payload:
        text = trailer_payload.decode("utf-8", errors="replace")
        for line in text.split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                trailers[k.strip().lower()] = v.strip()

    grpc_status = trailers.get("grpc-status", "0" if message_payload else "unknown")
    if grpc_status not in ("0", "unknown"):
        raise RuntimeError(
            f"gRPC-Web devolvió error: status={grpc_status} "
            f"message={trailers.get('grpc-message')}"
        )

    result = response_cls()
    if message_payload:
        result.ParseFromString(message_payload)
    return result


def main():
    print(f"Conectando a https://{HOST} (gRPC-Web) ...")

    req = api.ListApplicationsRequest(tenant_id=TENANT_ID, limit=20)
    resp = grpc_web_call(
        "api.ApplicationService", "List", req, api.ListApplicationsResponse
    )

    print(f"\n✅ Conexión OK. Aplicaciones encontradas: {resp.total_count}")
    for item in resp.result:
        print(f"  - {item.name}  (id={item.id})")

    if resp.result:
        first_app = resp.result[0]
        dreq = api.ListDevicesRequest(application_id=first_app.id, limit=20)
        dresp = grpc_web_call(
            "api.DeviceService", "List", dreq, api.ListDevicesResponse
        )

        print(f"\nDispositivos en '{first_app.name}': {dresp.total_count}")
        for d in dresp.result:
            last_seen = (
                d.last_seen_at.ToDatetime().isoformat()
                if d.last_seen_at.seconds
                else "Never"
            )
            print(f"  - {d.name}  DevEUI={d.dev_eui}  last_seen={last_seen}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        print("Copia este mensaje completo (y las líneas '->' de arriba) y pégamelo.")
