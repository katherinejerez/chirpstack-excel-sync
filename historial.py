"""
Historial diario de estado (Conectado/Desconectado/Pendiente) por dispositivo,
usado para armar la hoja "Resumen" del Excel diario.

Se guarda en ARCHIVO_HISTORIAL (JSON) y se commitea al repo desde el workflow
daily-email.yml -- igual que estado_actual.json en sync-chirpstack.yml -- así
persiste de una corrida a la otra aunque el runner de GitHub Actions sea
efímero.

Estructura del JSON:
  {"Ubicación|Entidad": {"2026-08-20": "Conectado", "2026-08-21": "Desconectado", ...}, ...}

Se conserva todo el historial (la hoja "Resumen" del Excel se organiza en una
hoja por mes, así que el ancho de cada hoja no crece con el tiempo). Si en
algún momento se prefiere acotar el archivo, se puede pasar `dias_retener`
a `actualizar_historial`.
"""

import json
import os

ARCHIVO_HISTORIAL = "historial_diario.json"


def cargar_historial(archivo=ARCHIVO_HISTORIAL):
    if not os.path.exists(archivo):
        return {}
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


def dias_ordenados(historial):
    """Todas las fechas (YYYY-MM-DD) presentes en el historial, ordenadas."""
    dias = set()
    for fechas in historial.values():
        dias.update(fechas.keys())
    return sorted(dias)


def actualizar_historial(filas, hoy, archivo=ARCHIVO_HISTORIAL, dias_retener=None):
    """Agrega el status de hoy para cada fila (id = 'ubicacion|entidad').
    Si se pasa `dias_retener`, recorta el historial a esa cantidad de días
    más recientes; por defecto no se recorta nada. Devuelve el historial ya
    actualizado y lo guarda en `archivo`."""
    historial = cargar_historial(archivo)

    for f in filas:
        id_ = f"{f['ubicacion']}|{f['entidad']}"
        historial.setdefault(id_, {})[hoy] = f["status"]

    if dias_retener:
        dias_a_conservar = set(dias_ordenados(historial)[-dias_retener:])
        for id_ in historial:
            historial[id_] = {d: s for d, s in historial[id_].items() if d in dias_a_conservar}

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2, sort_keys=True)

    return historial
