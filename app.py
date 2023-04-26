from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
import random
import time
import uuid

#from partida1 import Partida1
from partida2 import Partida2
#from partida3 import Partida3
#from partida4 import Partida4

app = FastAPI()

partidas1 = {}
partidas2 = {}
partidas3 = {}
partidas4 = {}
"""
#Partida de 1 jugador contra IA
@app.websocket("/partida1/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_id = str(uuid.uuid4())
    partida = Partida1()
    partidas1[partida_id] = partida

    await partida.set_player(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida.remove_player()
        partidas1.pop(partida_id)"""
        
#Partida de 2 jugadores        
@app.websocket("/partida2/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas2.values():
        if partida.jugadores < 2:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida2()
        partidas2[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas2.pop(partida_id)
"""
#Partida de 3 jugadores         
@app.websocket("/partida3/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas3.values():
        if partida.jugadores < 3:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida3()
        partidas3[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas3.pop(partida_id)
            
#Partida de 4 jugadores         
@app.websocket("/partida4/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas4.values():
        if partida.jugadores < 4:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida4()
        partidas4[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas4.pop(partida_id)

"""
