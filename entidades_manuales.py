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

RENOMBRES_HISTORICOS
----------------------
El historial (historial_diario.json) identifica cada dispositivo por su
DevEUI, así que un renombre en ChirpStack no le crea una fila nueva. Pero el
2026-08-07 se renombraron ~30 equipos en ChirpStack ANTES de que existiera
este esquema por DevEUI, así que ese historial viejo (2026-07-23 al
2026-08-06) quedó guardado con el nombre de esa época. Este mapeo (nombre
actual -> nombre viejo) se usa una sola vez, la primera vez que corre el
código nuevo, para pegar ese historial al dispositivo correcto en vez de
dejarlo como un equipo aparte (y en gris). Los pares se confirmaron
comparando, para cada Ubicación, la lista de equipos del 2026-08-06 vs.
2026-08-07 (mismo orden y mismo status ese día).
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

RENOMBRES_HISTORICOS = {
    # (ubicacion, nombre_actual_en_chirpstack): nombre_viejo_en_historial_diario.json
    ("Chimbarongo", "RAK2461_Energia_Decanters"): "Decantadores",
    ("Chimbarongo", "RAK2461_SE1_Flujo"): "Subestación 1",
    ("Chimbarongo", "RAK2470_SE2"): "Subestación 2",
    ("Chimbarongo", "RAK2470_York_Chico"): "York Chico",
    ("Cono Sur", "RAK2461_Centrifuga"): "Centrífuga",
    ("Cono Sur", "RAK2461_Climaveneta_2007"): "EAG-2007 (Climaveneta)",
    ("Cono Sur", "RAK2461_Climaveneta_2015"): "EAG-2015 (Climaveneta)",
    ("Cono Sur", "RAK2461_Climaveneta_ENF004"): "ENF004 (Climaveneta)",
    ("Cono Sur", "RAK2461_SE5"): "Subestación 5",
    ("Cono Sur", "RAK2470_Parabolico_1"): "Estación Parabólica 1 (Principal)",
    ("Cono Sur", "RAK2470_SE4"): "Subestación 4",
    ("Cono Sur", "RAK2470_York_2019_Mitsubishi"): "EAG-York 2019",
    ("Cono Sur", "RAK2470_York_2022"): "EAG-2022 (York)",
    ("Nueva Aurora", "RAK2461_Medidores_Y_Nivel"): "Medidor/Sensor Nivel",
    ("Nueva Aurora", "RAK2461_SE4"): "Subestación 4",
    ("Nueva Aurora", "RAK2461_York"): "York",
    ("Nueva Aurora", "RAK2470_Energia_Pozo"): "Energía Pozo",
    ("Nueva Aurora", "RAK2470_Flujometro"): "Red de Agua (Flujometro)",
    ("Nueva Aurora", "RAK2470_SE3"): "Subestación 3",
    ("Puente Alto", "RAK2461_Climaveneta_Frente"): "EAG-008 (Climaveneta Frente)",
    ("Puente Alto", "RAK2461_Don_Melchor"): "Nave 1 (Don Melchor)",
    ("Puente Alto", "RAK2461_Flujo_Bodega"): "Red de Agua (Flujo Bodega)",
    ("Puente Alto", "RAK2461_SE1"): "Subestación 1",
    ("Puente Alto", "RAK2470_Sala_Maquinas_1"): "EAG-04/5 (Sala de Maquinas 1)",
    ("Puente Alto", "RAK2470_Sala_Maquinas_2"): "Subestación 2 (Sala de Maquinas 2)",
    ("Vespucio", "RAK2461_Agua_Blanda"): "Agua Blanda",
    ("Vespucio", "RAK2461_Calderas"): "Calderas",
    ("Vespucio", "RAK2461_Nivel_Pozo"): "Nivel Pozo",
    ("Vespucio", "RAK2461_Techo"): "Subestación 1 (Techo)",
    ("Vespucio", "RAK2470_Bombas"): "Bombas",
    ("Vespucio", "RAK2470_Osmosis_Flujo"): "Planta Osmosis",
}
