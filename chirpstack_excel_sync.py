"""
Sincroniza el estado ("último dato recibido") de TODOS los dispositivos que
existen hoy en ChirpStack hacia estado_actual.json.

A diferencia de la versión anterior, ya no depende de una lista fija de
aplicaciones (APLICACIONES) ni de un mapeo manual Entidad -> DevEUI
(ENTIDAD_A_DEVEUI): descubre automáticamente todas las Ubicaciones
(aplicaciones) y Entidades (dispositivos) del tenant en ChirpStack vía
chirpstack_client.descubrir_todo(). Cuando se crea una ubicación nueva o se
agrega un equipo nuevo en ChirpStack, aparece solo en este archivo -- no hace
falta editar código para eso.

Los únicos ajustes manuales que se mantienen (equipos que comparten un mismo
DevEUI, o filas para equipos aún no dados de alta en ChirpStack) viven en
entidades_manuales.py.

Variables de entorno esperadas (como Secrets en GitHub Actions):
  CHIRPSTACK_API_TOKEN   -> token generado en ChirpStack (Tenant > API Keys)
"""

import os
import json

from chirpstack_client import descubrir_todo, calcular_estado
from entidades_manuales import DUPLICAR_ENTIDAD, FILAS_MANUALES, UBICACIONES_EXCLUIDAS

API_TOKEN = os.environ["CHIRPSTACK_API_TOKEN"]
ARCHIVO_SALIDA = "estado_actual.json"


def construir_filas(ahora=None):
    filas = []
    for d in descubrir_todo(API_TOKEN):
        if d["ubicacion"] in UBICACIONES_EXCLUIDAS:
            continue
        fecha, hora, status = calcular_estado(d["last_seen"], ahora=ahora)
        nombres = DUPLICAR_ENTIDAD.get(d["dev_eui"]) or [d["entidad"]]
        for nombre in nombres:
            filas.append({
                "id": f"{d['ubicacion']}|{nombre}",
                "fecha": fecha.isoformat() if fecha else "",
                "hora": hora.strftime("%H:%M:%S") if hora else "",
                "status": status,
            })

    for extra in FILAS_MANUALES:
        if extra["ubicacion"] in UBICACIONES_EXCLUIDAS:
            continue
        filas.append({
            "id": f"{extra['ubicacion']}|{extra['entidad']}",
            "fecha": "",
            "hora": "",
            "status": extra.get("status", "Pendiente"),
        })

    return filas


def main():
    filas = construir_filas()

    print(f"Total de filas a actualizar: {len(filas)}")
    for f in filas:
        print(f"  {f}")

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {ARCHIVO_SALIDA} ({len(filas)} filas).")


if __name__ == "__main__":
    main()
