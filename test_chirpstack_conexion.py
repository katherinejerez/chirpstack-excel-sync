"""
Script de PRUEBA — solo para confirmar que podemos hablar con ChirpStack
usando el token de API, directo por gRPC (sin necesitar un proxy REST).

Cómo usarlo:
1. pip install chirpstack-api grpcio
2. Reemplaza API_TOKEN abajo por tu token real (el que generaste en
   Tenant > API Keys), o expórtalo como variable de entorno:
     export CHIRPSTACK_API_TOKEN="tu_token_aqui"
3. Ejecuta: python3 test_chirpstack_conexion.py
4. Copia y pégame la salida completa (funcione o falle) para seguir.
"""

import os
import grpc
from chirpstack_api import api

HOST = "chirpstack-cyt.tecnoandina.cl"
PORT = 443
TENANT_ID = "7326cdb4-b1b2-4b35-ad5a-a5051f9c05e5"

API_TOKEN = os.environ.get("CHIRPSTACK_API_TOKEN", "PON_TU_TOKEN_AQUI")


def main():
    # Canal seguro (TLS) — igual que usa el navegador al entrar a la web de ChirpStack.
    channel = grpc.secure_channel(f"{HOST}:{PORT}", grpc.ssl_channel_credentials())
    auth_metadata = [("authorization", f"Bearer {API_TOKEN}")]

    print(f"Conectando a {HOST}:{PORT} ...")

    # 1) Listar aplicaciones del tenant (debería devolver Chimbarongo, Cono Sur, etc.)
    app_stub = api.ApplicationServiceStub(channel)
    req = api.ListApplicationsRequest(tenant_id=TENANT_ID, limit=20)
    resp = app_stub.List(req, metadata=auth_metadata, timeout=15)

    print(f"\n✅ Conexión OK. Aplicaciones encontradas: {resp.total_count}")
    for item in resp.result:
        print(f"  - {item.name}  (id={item.id})")

    # 2) Probar traer dispositivos de la primera aplicación encontrada
    if resp.result:
        first_app = resp.result[0]
        dev_stub = api.DeviceServiceStub(channel)
        dreq = api.ListDevicesRequest(application_id=first_app.id, limit=20)
        dresp = dev_stub.List(dreq, metadata=auth_metadata, timeout=15)

        print(f"\nDispositivos en '{first_app.name}': {dresp.total_count}")
        for d in dresp.result:
            last_seen = d.last_seen_at.ToDatetime().isoformat() if d.last_seen_at.seconds else "Never"
            print(f"  - {d.name}  DevEUI={d.dev_eui}  last_seen={last_seen}")


if __name__ == "__main__":
    try:
        main()
    except grpc.RpcError as e:
        print(f"\n❌ Error de gRPC: {e.code()} — {e.details()}")
        print("Copia este mensaje completo y pégamelo para diagnosticarlo.")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        print("Copia este mensaje completo y pégamelo para diagnosticarlo.")
