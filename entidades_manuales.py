"""
Ajustes manuales que se aplican ENCIMA del descubrimiento automático de
ChirpStack (ver chirpstack_client.py). Solo hace falta tocar este archivo
para estos casos puntuales; las ubicaciones y equipos nuevos que se agreguen
en ChirpStack aparecen solos en el Excel, sin editar nada acá.

DUPLICAR_ENTIDAD
-----------------
Casos ya existentes en que UN solo dispositivo físico (un DevEUI) reporta el
estado de varias filas/entidades del Excel (ej. una subestación que también
representa una línea fotovoltaica todavía sin equipo propio). Si un DevEUI
aparece acá, se generan filas con estos nombres en vez de una sola fila con
el nombre real del dispositivo en ChirpStack.

Se rescataron tal cual estaban en el mapeo manual anterior (ENTIDAD_A_DEVEUI)
para no perder ninguna fila del Excel actual al pasar al descubrimiento
automático.

FILAS_MANUALES
---------------
Filas para equipos que todavía NO están dados de alta en ChirpStack (sin
DevEUI). Quedan marcadas con el status indicado (por defecto "Pendiente")
hasta que se registre el dispositivo real en ChirpStack -- en ese momento
se puede borrar la entrada de acá, porque el dispositivo va a aparecer solo.

UBICACIONES_EXCLUIDAS
----------------------
Nombres de "Ubicación" (aplicación en ChirpStack) que no deben aparecer ni
en el Excel diario ni en el historial -- ej. aplicaciones de prueba que no
representan equipos reales en terreno.
"""

DUPLICAR_ENTIDAD = {
    # Cono Sur: un mismo dispositivo reporta el estado de 3 subestaciones y,
    # provisoriamente, también las 2 líneas fotovoltaicas (pendientes de
    # tener su propio DevEUI confirmado).
    "ac1f09fffe1b3248": [
        "Subestación 1",
        "Subestación 2",
        "Subestación 3",
        "Subestación 1 Fotovoltaica",
        "Subestación 2 Fotovoltaica",
    ],
    # Nueva Aurora: un mismo dispositivo reporta Subestación 1 y Subestación 2.
    "ac1f09fffe11ea24": [
        "Subestación 1",
        "Subestación 2",
    ],
}

FILAS_MANUALES = [
    # Ejemplo -- descomentar/editar cuando haya un equipo instalado pero
    # todavía sin configurar en ChirpStack:
    # {"ubicacion": "Limari", "entidad": "Subestación 3", "status": "Pendiente"},
]

UBICACIONES_EXCLUIDAS = {
    "TestOficina",
}
