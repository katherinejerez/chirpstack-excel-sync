"""
Genera una copia actualizada de Estado_conexiones.xlsx con los valores
más recientes de Fecha / Hora / Status obtenidos desde ChirpStack.

No modifica ningún archivo en OneDrive/SharePoint: crea un archivo nuevo
(con la fecha del día en el nombre) que luego el workflow de GitHub Actions
adjunta a un correo.

Variables de entorno esperadas:
  CHIRPSTACK_API_TOKEN   -> token generado en ChirpStack (Tenant > API Keys)
"""

import os
import struct
import requests
from datetime import datetime, timezone, timedelta
import openpyxl
from chirpstack_api import api

HOST = "chirpstack-cyt.tecnoandina.cl"
API_TOKEN = os.environ["CHIRPSTACK_API_TOKEN"]

PLANTILLA = "Estado_conexiones_template.xlsx"

TZ_CHILE = timezone(timedelta(hours=-4))  # ajustar a -3 en horario de verano
UMBRAL_DESCONEXION_MINUTOS = 5

APLICACIONES = {
    "Chimbarongo": "f06fa6b1-1ef5-4558-88bf-3998c36bf04b",
    "Cono Sur": "806685de-08e6-42de-b274-3b81b4531cee",
    "Limari": "9c7fa847-635c-42ac-96c8-82b2259b0306",
    "Nueva Aurora": "c4a0d671-07e1-4f1d-9617-cc2e8b1504b3",
    "Puente Alto": "7b7d81ae-16c4-44bc-abf3-589135c57979",
    "Vespucio": "f447c27d-8f44-48d2-b6a0-11e4fbea62a3",
}

ENTIDAD_A_DEVEUI = {
    "Chimbarongo|Decantadores": "ac1f09fffe1b32ba",
    "Chimbarongo|Subestación 1": "ac1f09fffe1ce6bf",
    "Chimbarongo|Subestación 2": "ac1f09fffe11ea46",
    "Chimbarongo|York Chico": "ac1f09fffe128532",
    "Cono Sur|Centrífuga": "ac1f09fffe1ce77f",
    "Cono Sur|EAG-2007 (Climaveneta)": "ac1f09fffe1ce719",
    "Cono Sur|EAG-2015 (Climaveneta)": "ac1f09fffe1ce74c",
    "Cono Sur|ENF004 (Climaveneta)": "ac1f09fffe1b324e",
    "Cono Sur|Subestación 1": "ac1f09fffe1b3248",
    "Cono Sur|Subestación 2": "ac1f09fffe1b3248",
    "Cono Sur|Subestación 3": "ac1f09fffe1b3248",
    "Cono Sur|Subestación 5": "ac1f09fffe1ce6e0",
    "Cono Sur|EAG-2022 (York)": "ac1f09fffe11ea15",
    "Cono Sur|Estación Parabólica 1 (Principal)": "ac1f09fffe12849d",
    "Cono Sur|Subestación 4": "ac1f09fffe128476",
    "Cono Sur|EAG-York 2019": "ac1f09fffe128493",
    "Cono Sur|Subestación 1 Fotovoltaica": "ac1f09fffe1b3248",
    "Cono Sur|Subestación 2 Fotovoltaica": "ac1f09fffe1b3248",
    "Limari|Energía EAG-0019 (Climaveneta)": "ac1f09fffe1b32b3",
    "Limari|Energía EAG-0047": "ac1f09fffe1b32ce",
    "Limari|Subestación 1": "ac1f09fffe11ea53",
    "Limari|Subestación 2": "ac1f09fffe11ea4d",
    "Nueva Aurora|Medidor/Sensor Nivel": "ac1f09fffe1ce70f",
    "Nueva Aurora|Subestación 4": "ac1f09fffe1b32a0",
    "Nueva Aurora|York": "ac1f09fffe1ce744",
    "Nueva Aurora|Energía Pozo": "ac1f09fffe11ea05",
    "Nueva Aurora|Red de Agua (Flujometro)": "ac1f09fffe11ea37",
    "Nueva Aurora|Subestación 1": "ac1f09fffe11ea24",
    "Nueva Aurora|Subestación 2": "ac1f09fffe11ea24",
    "Nueva Aurora|Subestación 3": "ac1f09fffe11ea00",
    "Puente Alto|EAG-008 (Climaveneta Frente)": "ac1f09fffe1b327a",
    "Puente Alto|Nave 1 (Don Melchor)": "ac1f09fffe1b32a2",
    "Puente Alto|Red de Agua (Flujo Bodega)": "ac1f09fffe1b3288",
    "Puente Alto|Subestación 1": "ac1f09fffe1b3273",
    "Puente Alto|EAG-04/5 (Sala de Maquinas 1)": "ac1f09fffe1284b0",
    "Puente Alto|Subestación 2 (Sala de Maquinas 2)": "ac1f09fffe11e9ac",
    "Vespucio|Calderas": "ac1f09fffe1b3279",
    "Vespucio|Agua Blanda": "ac1f09fffe1b328e",
    "Vespucio|Nivel Pozo": "ac1f09fffe1b320d",
    "Vespucio|Subestación 1 (Techo)": "ac1f09fffe1b3263",
    "Vespucio|Bombas": "ac1f09fffe1284a4",
    "Vespucio|Planta Osmosis": "ac1f09fffe11ea16",
}


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


def grpc_web_call(service, method, request_message, response_cls, timeout=15):
    url = f"https://{HOST}/{service}/{method}"
    body = _frame(request_message.SerializeToString())
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "Accept": "application/grpc-web+proto",
        "X-Grpc-Web": "1",
        "Authorization": f"Bearer {API_TOKEN}",
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


def obtener_dispositivos(application_id):
    resultado = {}
    offset = 0
    while True:
        req = api.ListDevicesRequest(application_id=application_id, limit=100, offset=offset)
        resp = grpc_web_call("api.DeviceService", "List", req, api.ListDevicesResponse)
        for d in resp.result:
            last_seen = d.last_seen_at.ToDatetime(tzinfo=timezone.utc) if d.last_seen_at.seconds else None
            resultado[d.dev_eui] = last_seen
        if len(resp.result) < 100:
            break
        offset += 100
    return resultado


def main():
    deveui_a_ids = {}
    for id_fila, deveui in ENTIDAD_A_DEVEUI.items():
        deveui_a_ids.setdefault(deveui, []).append(id_fila)

    ahora = datetime.now(timezone.utc)
    valores_por_id = {}  # id_fila -> (fecha, hora, status)

    for ubicacion, app_id in APLICACIONES.items():
        print(f"Consultando '{ubicacion}' ...")
        dispositivos = obtener_dispositivos(app_id)
        for deveui, last_seen in dispositivos.items():
            ids_relacionados = deveui_a_ids.get(deveui)
            if not ids_relacionados:
                continue
            if last_seen is None:
                status, fecha, hora = "Desconectado", None, None
            else:
                minutos_desde = (ahora - last_seen).total_seconds() / 60
                status = "Conectado" if minutos_desde <= UMBRAL_DESCONEXION_MINUTOS else "Desconectado"
                local = last_seen.astimezone(TZ_CHILE)
                fecha, hora = local.date(), local.time()
            for id_fila in ids_relacionados:
                valores_por_id[id_fila] = (fecha, hora, status)

    wb = openpyxl.load_workbook(PLANTILLA)
    ws = wb["Hoja1"]
    actualizadas = 0
    for row in range(3, 45):
        id_fila = ws.cell(row=row, column=7).value
        if id_fila in valores_por_id:
            fecha, hora, status = valores_por_id[id_fila]
            if fecha is not None:
                ws.cell(row=row, column=3).value = fecha
                ws.cell(row=row, column=4).value = hora
            ws.cell(row=row, column=5).value = status
            actualizadas += 1

    hoy = datetime.now(TZ_CHILE).strftime("%Y-%m-%d")
    nombre_salida = f"Estado_conexiones_{hoy}.xlsx"
    wb.save(nombre_salida)
    print(f"\n✅ {actualizadas} filas actualizadas. Archivo generado: {nombre_salida}")

    # Deja el nombre disponible para el siguiente paso del workflow (adjuntar al correo)
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"archivo={nombre_salida}\n")


if __name__ == "__main__":
    main()
