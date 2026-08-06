"""
Cliente ChirpStack (gRPC-Web) compartido por los scripts de sincronización.

A diferencia de la versión anterior, este módulo DESCUBRE automáticamente
todas las aplicaciones ("Ubicación" en el Excel) y todos los dispositivos
("Entidad" en el Excel) que existen en el tenant de ChirpStack, en vez de
depender de un diccionario fijo mantenido a mano (APLICACIONES /
ENTIDAD_A_DEVEUI). Cuando se crea una ubicación nueva o se agrega un equipo
nuevo en ChirpStack, aparece solo la próxima vez que corre el workflow --no
hace falta editar código para eso.

Usa gRPC-Web (mismo protocolo que usa el navegador para hablar con la UI de
ChirpStack); el gRPC nativo no funciona en el puerto público de este
servidor (ya se había confirmado con pruebas anteriores).
"""

import os
import struct
import requests
from datetime import datetime, timezone, timedelta
from chirpstack_api import api

HOST = os.environ.get("CHIRPSTACK_HOST", "chirpstack-cyt.tecnoandina.cl")

# Tenant "Tecnoandina" en ChirpStack (confirmado con test_chirpstack_conexion.py).
# Se puede sobrescribir con la variable de entorno CHIRPSTACK_TENANT_ID si
# alguna vez hiciera falta apuntar a otro tenant.
TENANT_ID = os.environ.get("CHIRPSTACK_TENANT_ID", "7326cdb4-b1b2-4b35-ad5a-a5051f9c05e5")

# Zona horaria de Chile continental (ajustar si corresponde horario de verano distinto).
TZ_CHILE = timezone(timedelta(hours=-4))

# Si un dispositivo no reporta hace más de este tiempo, se marca "Desconectado".
UMBRAL_DESCONEXION_MINUTOS = 5


def _frame(payload: bytes) -> bytes:
    return struct.pack(">BI", 0, len(payload)) + payload


def _parse_frames(body: bytes):
    frames, i = [], 0
    while i + 5 <= len(body):
        flag = body[i]
        length = struct.unpack(">I", body[i + 1:i + 5])[0]
        frames.append((flag, body[i + 5:i + 5 + length]))
        i += 5 + length
    return frames


def grpc_web_call(token, service, method, request_message, response_cls, timeout=15):
    url = f"https://{HOST}/{service}/{method}"
    body = _frame(request_message.SerializeToString())
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "Accept": "application/grpc-web+proto",
        "X-Grpc-Web": "1",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.post(url, data=body, headers=headers, timeout=timeout)
    resp.raise_for_status()

    message_payload, trailer_payload = None, None
    for flag, payload in _parse_frames(resp.content):
        if flag & 0x80:
            trailer_payload = payload
        else:
            message_payload = payload

    trailers = {}
    if trailer_payload:
        for line in trailer_payload.decode("utf-8", errors="replace").split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                trailers[k.strip().lower()] = v.strip()

    grpc_status = trailers.get("grpc-status", "0" if message_payload else "unknown")
    if grpc_status not in ("0", "unknown"):
        raise RuntimeError(f"gRPC-Web error: status={grpc_status} message={trailers.get('grpc-message')}")

    result = response_cls()
    if message_payload:
        result.ParseFromString(message_payload)
    return result


def listar_aplicaciones(token, tenant_id=None):
    """Todas las aplicaciones (Ubicaciones) del tenant, paginando de a 100."""
    tenant_id = tenant_id or TENANT_ID
    aplicaciones = []
    offset = 0
    while True:
        req = api.ListApplicationsRequest(tenant_id=tenant_id, limit=100, offset=offset)
        resp = grpc_web_call(token, "api.ApplicationService", "List", req, api.ListApplicationsResponse)
        for item in resp.result:
            aplicaciones.append({"id": item.id, "nombre": item.name})
        if len(resp.result) < 100:
            break
        offset += 100
    return aplicaciones


def listar_dispositivos(token, application_id):
    """Todos los dispositivos (Entidades) de una aplicación, paginando de a 100."""
    dispositivos = []
    offset = 0
    while True:
        req = api.ListDevicesRequest(application_id=application_id, limit=100, offset=offset)
        resp = grpc_web_call(token, "api.DeviceService", "List", req, api.ListDevicesResponse)
        for d in resp.result:
            last_seen = d.last_seen_at.ToDatetime(tzinfo=timezone.utc) if d.last_seen_at.seconds else None
            dispositivos.append({"dev_eui": d.dev_eui, "nombre": d.name, "last_seen": last_seen})
        if len(resp.result) < 100:
            break
        offset += 100
    return dispositivos


def calcular_estado(last_seen, ahora=None):
    """(fecha, hora, status) en hora de Chile a partir del último dato (datetime UTC o None)."""
    ahora = ahora or datetime.now(timezone.utc)
    if last_seen is None:
        return None, None, "Desconectado"
    minutos_desde = (ahora - last_seen).total_seconds() / 60
    status = "Conectado" if minutos_desde <= UMBRAL_DESCONEXION_MINUTOS else "Desconectado"
    local = last_seen.astimezone(TZ_CHILE)
    return local.date(), local.time(), status


def descubrir_todo(token, tenant_id=None):
    """
    Recorre TODAS las aplicaciones y dispositivos del tenant en ChirpStack.

    Devuelve una lista de dicts:
      {"ubicacion": <nombre de la aplicación>,
       "entidad": <nombre del dispositivo>,
       "dev_eui": ...,
       "last_seen": datetime UTC | None}

    'ubicacion' y 'entidad' salen tal cual están registrados en ChirpStack:
    no hace falta mantener ningún mapeo a mano para que un dispositivo nuevo
    aparezca acá.
    """
    filas = []
    for app in listar_aplicaciones(token, tenant_id):
        for d in listar_dispositivos(token, app["id"]):
            filas.append({
                "ubicacion": app["nombre"],
                "entidad": d["nombre"] or d["dev_eui"],
                "dev_eui": d["dev_eui"],
                "last_seen": d["last_seen"],
            })
    return filas
