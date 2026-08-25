"""
Reconstruye historial_diario.json a partir del historial de git de
estado_actual.json (que sync-chirpstack.yml commitea cada vez que cambia el
status de algún dispositivo, desde el 2026-07-23).

Para cada día calendario (hora de Chile) desde ese inicio hasta hoy, busca el
commit más cercano a las 09:00 hora Chile -- la misma hora a la que apunta el
envío diario -- y usa el estado_actual.json de ese commit como "foto" del día.

Es una herramienta de recuperación / migración: se puede volver a correr en
cualquier momento (mientras no se reescriba la historia de git) para
regenerar historial_diario.json desde cero, por ejemplo si el archivo se
corrompe o si se quiere ampliar la ventana reconstruida.

Uso:
  python backfill_historial.py
"""

import json
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from entidades_manuales import UBICACIONES_EXCLUIDAS
from historial import ARCHIVO_HISTORIAL

TZ_CHILE = ZoneInfo("America/Santiago")
HORA_OBJETIVO = 9  # hora local a la que apunta el envío diario
ARCHIVO_SEGUIMIENTO = "estado_actual.json"


def listar_commits():
    """[(hash, datetime UTC-aware), ...] para estado_actual.json, más viejo primero."""
    salida = subprocess.run(
        ["git", "log", "--follow", "--format=%H %cI", "--", ARCHIVO_SEGUIMIENTO],
        capture_output=True, text=True, check=True,
    ).stdout
    commits = []
    for linea in salida.strip().splitlines():
        hash_, fecha_iso = linea.split(" ", 1)
        commits.append((hash_, datetime.fromisoformat(fecha_iso)))
    commits.reverse()  # más viejo primero
    return commits


def elegir_commit_por_dia(commits):
    """Para cada día calendario (hora Chile) con al menos un commit, el más
    cercano a las HORA_OBJETIVO:00 hora Chile. Devuelve {fecha_iso: hash}."""
    por_dia = {}
    for hash_, fecha_utc in commits:
        local = fecha_utc.astimezone(TZ_CHILE)
        dia = local.date().isoformat()
        objetivo = local.replace(hour=HORA_OBJETIVO, minute=0, second=0, microsecond=0)
        diff = abs((local - objetivo).total_seconds())
        if dia not in por_dia or diff < por_dia[dia][1]:
            por_dia[dia] = (hash_, diff)
    return {dia: hash_ for dia, (hash_, _diff) in por_dia.items()}


def leer_estado_en_commit(hash_):
    # OJO: estado_actual.json se escribe en UTF-8 (nombres con tildes/ñ). Sin
    # encoding="utf-8" explícito, subprocess decodifica con el encoding por
    # defecto del sistema (cp1252 en Windows) y corrompe esos caracteres.
    salida = subprocess.run(
        ["git", "show", f"{hash_}:{ARCHIVO_SEGUIMIENTO}"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return json.loads(salida)


def main():
    commits = listar_commits()
    print(f"{len(commits)} commits encontrados para {ARCHIVO_SEGUIMIENTO}.")

    commit_por_dia = elegir_commit_por_dia(commits)
    dias = sorted(commit_por_dia)
    print(f"Reconstruyendo {len(dias)} días, desde {dias[0]} hasta {dias[-1]}.\n")

    historial = {}
    for dia in dias:
        estado = leer_estado_en_commit(commit_por_dia[dia])
        for entrada in estado:
            ubicacion = entrada["id"].split("|", 1)[0]
            if ubicacion in UBICACIONES_EXCLUIDAS:
                continue
            historial.setdefault(entrada["id"], {})[dia] = entrada["status"]
        print(f"  {dia}: {len(estado)} dispositivos (commit {commit_por_dia[dia][:7]})")

    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n{ARCHIVO_HISTORIAL} reconstruido con {len(historial)} dispositivos "
          f"y {len(dias)} días de historia.")


if __name__ == "__main__":
    main()
