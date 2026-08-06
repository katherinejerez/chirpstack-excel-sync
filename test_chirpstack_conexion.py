"""
Script de PRUEBA -- verifica la conexión a ChirpStack y muestra qué
Ubicaciones (aplicaciones) y Entidades (dispositivos) descubre automáticamente
el mismo código que usan chirpstack_excel_sync.py y generar_excel_diario.py.

Útil para confirmar, antes de esperar al workflow programado, que un tenant,
ubicación o equipo nuevo en ChirpStack ya se está reconociendo solo.

Cómo usarlo (en GitHub Actions, vía el workflow test-chirpstack.yml):
- Correr el workflow "Run workflow" (usa el secreto CHIRPSTACK_API_TOKEN que
  ya está configurado).
"""

import os

from chirpstack_client import listar_aplicaciones, listar_dispositivos, TENANT_ID, HOST

API_TOKEN = os.environ.get("CHIRPSTACK_API_TOKEN", "PON_TU_TOKEN_AQUI")


def main():
    print(f"Conectando a https://{HOST} (gRPC-Web), tenant={TENANT_ID} ...")

    aplicaciones = listar_aplicaciones(API_TOKEN)
    print(f"\n✅ Conexión OK. Aplicaciones (Ubicaciones) encontradas: {len(aplicaciones)}")

    total_dispositivos = 0
    for app in aplicaciones:
        dispositivos = listar_dispositivos(API_TOKEN, app["id"])
        total_dispositivos += len(dispositivos)
        print(f"\n- {app['nombre']}  (id={app['id']})  -- {len(dispositivos)} dispositivo(s):")
        for d in dispositivos:
            last_seen = d["last_seen"].isoformat() if d["last_seen"] else "Never"
            print(f"    · {d['nombre']}  DevEUI={d['dev_eui']}  last_seen={last_seen}")

    print(f"\nTotal: {len(aplicaciones)} ubicaciones, {total_dispositivos} dispositivos.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        print("Copia este mensaje completo y pégamelo.")
