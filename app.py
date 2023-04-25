from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from logica_juego import crear_mazo, repartir_cartas, que_jugador_gana_baza, sumar_puntos, que_cartas_puede_usar_jugador_arrastre
import random


#TODO almacenar nombre usuario juagdor
app = FastAPI()

sockets = {}
socket0_received = asyncio.Event()
socket1_received = asyncio.Event()

message_socket = None

async def main_program():
    global message_socket
    
    while True:
        
        while len(sockets) < 2:
            await asyncio.sleep(1)
                
        puntosJugador0 = 0
        puntosJugador1 = 0
        
        orden_inicial = [0,1]
        orden = [0,1]
        
        vueltas = False
        
        for i in range(2):
            
            manos = []
            mazo, triunfo, manos = await comienzo_partida()
            
            for i in range(14):
                puntosJugador0, puntosJugador1, manos, orden, orden_inicial = await ronda(triunfo, puntosJugador0, puntosJugador1, manos, orden, orden_inicial)    
                if vueltas: 
                    ganador = comprobarGanador(puntosJugador0, puntosJugador1)
                    if ganador: break
                mazo, manos = await repartir(orden_inicial, mazo, triunfo, manos)
            
            await send_message_to_all_sockets("Arrastre")
            
            for i in range(6):
                await mandar_manos(orden_inicial, manos)
                orden, manos, puntosJugador0, puntosJugador1, indice_ganador = await arrastre(orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, manos)
                if vueltas: 
                    ganador = comprobarGanador(puntosJugador0, puntosJugador1)
                    if ganador: break
                
            if puntosJugador0 > 100 and puntosJugador1 < 100:
                mano_send = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)                        
                await send_message_to_all_sockets(message)
                break
            elif puntosJugador1 > 100 and puntosJugador0 < 100:
                mano_send = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)
                await send_message_to_all_sockets(message)
                break
            elif puntosJugador0 > 100 and puntosJugador1 > 100:
                if orden[indice_ganador] == orden_inicial[0]: 
                    mano_send = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                    message = json.dumps(mano_send)  
                    await send_message_to_all_sockets(message)
                    break
                else:
                    mano_send = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                    message = json.dumps(mano_send)
                    await send_message_to_all_sockets(message)
                    break
            else:
                vueltas = True
                mano_send = {"Ganador": None, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)
                await send_message_to_all_sockets(message)


        
@app.websocket("/socket/0/{client_id}")
async def websocket_endpoint_socket1(websocket: WebSocket, client_id: str):
        global message_socket
        await websocket.accept()
        sockets["socket0"] = websocket  
        try:
            while True:
                message_socket = await websocket.receive_text()
                socket0_received.set()
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            sockets.pop("socket0", None)

@app.websocket("/socket/1/{client_id}")
async def websocket_endpoint_socket2(websocket: WebSocket, client_id: str):
    global message_socket
    await websocket.accept()
    sockets["socket1"] = websocket  
    try:
        while True:
            message_socket = await websocket.receive_text()
            socket1_received.set()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        sockets.pop("socket1", None)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(main_program())
    
async def send_message_to_all_sockets(message: str):
    for websocket in sockets.values():
        await websocket.send_text(message)
        
async def await_message(id: str):
    if id == "0":
        await socket0_received.wait()
        socket0_received.clear()
    else:
        await socket1_received.wait()
        socket1_received.clear()
        
async def send_message_to_socket(socketid: str, message: str):
    websocket = sockets.get("socket" + socketid)
    if websocket:
        await websocket.send_text(message)

async def comienzo_partida():
    mazo = crear_mazo()
    random.shuffle(mazo)
    manos, mazo = repartir_cartas(mazo, 2)
    triunfo = mazo[0]
    mazo.remove(triunfo)
    
    # Repartir manos a los jugadores
    for i in range(2):
        mano_send = {"Cartas": manos[i], "Triunfo": triunfo ,"Jugador": i}
        message = json.dumps(mano_send)
        await send_message_to_socket(str(i), message)
        
    return mazo, triunfo, manos

async def ronda(triunfo, puntosJugador0, puntosJugador1, manos, orden, orden_inicial):
    cartas_jugadas = [None, None]
    puntuacion_cartas = []
    global message_socket
    cartas_jugadas_mandar = [None, None]
    
    for i in range(2):
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": triunfo}
        message = json.dumps(mano_send)
        await send_message_to_all_sockets(message)
        
        await await_message(str(orden[i]))
        
        carta = message_socket
                 
        palo, valor = carta.split("-") 
        carta_tupla = (palo, int(valor))

                
        manos[orden[i]].remove(carta_tupla)
        cartas_jugadas[i] = carta_tupla
        cartas_jugadas_mandar[orden[i]] = carta_tupla
        puntuacion_cartas.append(carta_tupla)
    
    mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": None, "Triunfo": triunfo}
    message = json.dumps(mano_send)
    await send_message_to_all_sockets(message)
    
    carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
    indice_ganador = puntuacion_cartas.index(carta_gandora)
    
    #Sumo puntos al jugador que ha ganado la baza
    if orden[indice_ganador] == orden_inicial[0]:
        puntosJugador0 += sumar_puntos(cartas_jugadas)
        await send_message_to_all_sockets("Ganador: 0")
    else:
        puntosJugador1 += sumar_puntos(cartas_jugadas)
        await send_message_to_all_sockets("Ganador: 1")
        
    #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
    if indice_ganador == 1:
        orden = list(reversed(orden))
                
    return puntosJugador0, puntosJugador1, manos, orden, orden_inicial

async def repartir(orden_inicial, mazo, triunfo, manos):
    for i in orden_inicial:
        if len(mazo) == 0:
            carta_robada = triunfo
        else:
            carta_robada = mazo[0]
            mazo.remove(carta_robada)
        manos[i].append(carta_robada)
        mano_send = manos[i]
        message = json.dumps(mano_send)
        await send_message_to_socket(str(i), message)
    
    return mazo, manos

async def arrastre(orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, manos):
    cartas_jugadas = [None, None]
    cartas_jugadas_mandar = [None, None]
    puntuacion_cartas = []
    global message_socket
    
    for i in range(2):
        #si eres el primero en tirar puedes usar lo que quieras
        if i == 0:
            mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": None}
            message = json.dumps(mano_send)
            await send_message_to_all_sockets(message)
            
            mano_send = manos[orden[i]]
            message = json.dumps(mano_send)
            await send_message_to_socket(str(orden[i]), message)
        else:
            mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": None}
            message = json.dumps(mano_send)
            await send_message_to_all_sockets(message)   
                     
            cartas_posibles = que_cartas_puede_usar_jugador_arrastre(manos[orden[i]], puntuacion_cartas, triunfo)
            message = json.dumps(cartas_posibles)
            await send_message_to_socket(str(orden[i]), message)
        
        await await_message(str(orden[i]))
        
        carta = message_socket
                 
        palo, valor = carta.split("-") 
        carta_tupla = (palo, int(valor))
                
        manos[orden[i]].remove(carta_tupla)
        cartas_jugadas[i] = carta_tupla
        cartas_jugadas_mandar[orden[i]] = carta_tupla
        puntuacion_cartas.append(carta_tupla)
        
    mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": None, "Triunfo": None}
    message = json.dumps(mano_send)
    await send_message_to_all_sockets(message)  
        
    carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
    indice_ganador = puntuacion_cartas.index(carta_gandora)
    
    #Sumo puntos al jugador que ha ganado la baza
    if orden[indice_ganador] == orden_inicial[0]:
        puntosJugador0 += sumar_puntos(cartas_jugadas)
        await send_message_to_all_sockets("Ganador: 0")
    else:
        puntosJugador1 += sumar_puntos(cartas_jugadas)
        await send_message_to_all_sockets("Ganador: 1")
        
    #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
    if indice_ganador == 1:
        orden = orden[1:] + orden[:1]
    
    return orden, manos, puntosJugador0, puntosJugador1, indice_ganador 

async def comprobarGanador(puntosJugador0, puntosJugador1):
    if puntosJugador0 >= 100:
        message = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
        message = json.dumps(message)
        await send_message_to_all_sockets(message)
        return True
    elif puntosJugador1 >= 100:
        message = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
        message = json.dumps(message)
        await send_message_to_all_sockets(message)
        return True
    else:
        return False

async def mandar_manos(orden_inicial, manos):
    for i in orden_inicial:
        mano_send = manos[i]
        message = json.dumps(mano_send)
        await send_message_to_socket(str(i), message)
    
