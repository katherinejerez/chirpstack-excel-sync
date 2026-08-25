"""
Historial diario de estado (Conectado/Desconectado/Pendiente) por dispositivo,
usado para armar la hoja "Resumen" del Excel diario.

Se guarda en ARCHIVO_HISTORIAL (JSON) y se commitea al repo desde el workflow
daily-email.yml -- igual que estado_actual.json en sync-chirpstack.yml -- así
persiste de una corrida a la otra aunque el runner de GitHub Actions sea
efímero.

Cada dispositivo se identifica por su DevEUI (campo "clave_historial" en las
filas que arma generar_excel_diario.py), NO por su nombre: así, si el equipo
se renombra en ChirpStack, sigue siendo la misma fila del historial en vez de
aparecer como un dispositivo nuevo (dejando la fila del nombre viejo en gris
para siempre). El nombre mostrado en la hoja "Resumen" siempre es el más
reciente que reportó ChirpStack.

Estructura del JSON:
  {"<DevEUI o clave manual>": {
      "nombre": "Ubicación|Entidad" (el más reciente),
      "dias": {"2026-08-20": "Conectado", "2026-08-21": "Desconectado", ...}
   }, ...}
"""

import json
import os

from entidades_manuales import RENOMBRES_HISTORICOS

ARCHIVO_HISTORIAL = "historial_diario.json"


def cargar_historial(archivo=ARCHIVO_HISTORIAL):
    if not os.path.exists(archivo):
        return {}
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


def _es_formato_viejo(historial):
    """El formato viejo guardaba directamente {fecha: status} en cada
    entrada, con "Ubicación|Entidad" (el nombre de ese momento) como clave."""
    return any("dias" not in entrada for entrada in historial.values())


def _migrar_formato_viejo(historial_viejo, filas_hoy):
    """Convierte un historial en formato viejo (clave = nombre) al formato
    nuevo (clave = DevEUI), usando las filas de hoy -- que sí tienen DevEUI
    real -- para saber a qué clave nueva corresponde cada nombre. Para el
    historial de antes del 2026-08-07 (cuando se renombraron varios equipos
    en ChirpStack), usa RENOMBRES_HISTORICOS para encontrar el nombre viejo
    correspondiente."""
    nuevo = {}
    consumidos = set()

    for f in filas_hoy:
        clave = f["clave_historial"]
        nombre_actual = f"{f['ubicacion']}|{f['entidad']}"
        dias = {}

        if nombre_actual in historial_viejo:
            dias.update(historial_viejo[nombre_actual])
            consumidos.add(nombre_actual)

        nombre_viejo = RENOMBRES_HISTORICOS.get((f["ubicacion"], f["entidad"]))
        if nombre_viejo:
            id_viejo = f"{f['ubicacion']}|{nombre_viejo}"
            if id_viejo in historial_viejo:
                dias.update(historial_viejo[id_viejo])
                consumidos.add(id_viejo)

        nuevo[clave] = {"nombre": nombre_actual, "dias": dias}

    # Equipos que ya no existen hoy en ChirpStack y no calzan con ningún
    # renombre conocido: se conservan tal cual (con su nombre viejo como
    # clave y como nombre) para no perder su historia.
    for id_viejo, dias in historial_viejo.items():
        if id_viejo not in consumidos:
            nuevo[id_viejo] = {"nombre": id_viejo, "dias": dict(dias)}

    return nuevo


def dias_ordenados(historial):
    """Todas las fechas (YYYY-MM-DD) presentes en el historial, ordenadas."""
    dias = set()
    for entrada in historial.values():
        dias.update(entrada["dias"].keys())
    return sorted(dias)


def actualizar_historial(filas, hoy, archivo=ARCHIVO_HISTORIAL):
    """Agrega el status de hoy para cada fila (clave = f['clave_historial'],
    típicamente el DevEUI). Devuelve el historial ya actualizado y lo guarda
    en `archivo`."""
    historial = cargar_historial(archivo)

    if historial and _es_formato_viejo(historial):
        historial = _migrar_formato_viejo(historial, filas)

    for f in filas:
        clave = f["clave_historial"]
        entrada = historial.setdefault(clave, {"nombre": None, "dias": {}})
        entrada["nombre"] = f"{f['ubicacion']}|{f['entidad']}"
        entrada["dias"][hoy] = f["status"]

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2, sort_keys=True)

    return historial
