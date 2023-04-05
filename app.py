from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from logica_juego import crear_mazo, repartir_cartas, que_jugador_gana_baza, sumar_puntos, que_cartas_puede_usar_jugador_arrastre
import random
import asyncio
import json
import time

app = FastAPI()

players_connected = {}
jugadores = {}

puntosJugador0 = 0
puntosJugador1 = 0

#TODO en las idas si ambos lelgan a 100, que gane el de las 10 ultimas

#async def partida2(direccion, app):
#TODO hacer que sea una funcino que le llame el main    
@app.websocket("/partidaX/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            final = False
            players_connected[client_id] = websocket
            message = await websocket.receive_text()
            print(f'Mensaje recibido del cliente {client_id}: {message}')
            if len(players_connected) == 2:
                puntosJugador0 = 0
                puntosJugador1 = 0
                for modo in range(2):
                    #TODOD quitar este mensaje
                    mazo, triunfo, jugadores_inicial, jugadores, manos = await comienzo_partida(players_connected)
                    for i in range(14):
                        jugadores, puntosJugador0, puntosJugador0, manos = await ronda(jugadores_inicial, jugadores, 
                                                        players_connected, triunfo, puntosJugador0, puntosJugador0, websocket, manos)
                        if modo == 2:
                            if comprobarGanador(puntosJugador0, puntosJugador0):
                                final = True
                                break
                        mazo, manos = await repartir(jugadores_inicial, mazo, triunfo, manos)    
                        
                    #TODO porque el mensaje de arrastre se manda antes que las manos
                    await send_to_all_clients("Arrastre", players_connected)
                    
                    if not final:
                        for i in range(6):
                            jugadores, manos, puntosJugador0, puntosJugador1, indice_ganador = await arrastre(websocket, jugadores_inicial, jugadores, players_connected, triunfo, puntosJugador0, puntosJugador1, manos)
                            if modo == 2:
                                if comprobarGanador(puntosJugador0, puntosJugador0): 
                                    break
                        
                    if puntosJugador0 > 100 and puntosJugador1 < 100:
                        mano_send = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                        message = json.dumps(mano_send)                        
                        await send_to_all_clients(message, players_connected)
                        break
                    elif puntosJugador1 > 100 and puntosJugador0 < 100:
                        mano_send = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                        message = json.dumps(mano_send)
                        await send_to_all_clients(message, players_connected)
                        break
                    elif puntosJugador0 > 100 and puntosJugador1 > 100:
                        if jugadores[indice_ganador] == jugadores_inicial[0]: 
                            mano_send = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                            message = json.dumps(mano_send)  
                            await send_to_all_clients(message, players_connected)
                            break
                        else:
                            mano_send = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                            message = json.dumps(mano_send)
                            await send_to_all_clients(message, players_connected)
                            break
                    else:
                        mano_send = {"Ganador": None, "0": puntosJugador0 ,"1": puntosJugador1}
                        message = json.dumps(mano_send)
                        await send_to_all_clients(message, players_connected)                    
                        
                    #TODO meter datos de partidas y puntos y esas cosas en la bd

            else:
                #TODO si se desconecta un jugador, que hacer
                await websocket.send_text("espera")
        
    except WebSocketDisconnect:
        print("Exception")
        
async def comienzo_partida(players_connected):
    mazo = crear_mazo()
    random.shuffle(mazo)
    manos, mazo = repartir_cartas(mazo, 2)
    triunfo = mazo[0]
    mazo.remove(triunfo)
    jugadores = list(players_connected)
    jugadores_inicial = list(players_connected)
    
    # Repartir manos a los jugadores
    for i, player_id in enumerate(jugadores):
        mano_send = {"Cartas": manos[i], "Triunfo": triunfo ,"Jugador": i}
        message = json.dumps(mano_send)
        asyncio.create_task(send_to_single_client(player_id, message, players_connected))
        
    return mazo, triunfo, jugadores_inicial, jugadores, manos
        
async def ronda(jugadores_inicial, jugadores, players_connected, triunfo, puntosJugador0, puntosJugador1, websocket, manos):
    cartas_jugadas = [None, None]
    puntuacion_cartas = []
    #Que cada jugador juegue una carta
    for i, player_id in enumerate(jugadores):
        indice = 0
        if jugadores[i] == jugadores_inicial[1]:
            indice = 1
        mano_send = {"0": cartas_jugadas[0], "1": cartas_jugadas[1] ,"Turno": indice, "Triunfo": triunfo}
        message = json.dumps(mano_send)
        asyncio.create_task(send_to_all_clients(message, players_connected))
                
        carta = await websocket.receive_text()
        if carta[0] !=  "N":
            break
        
        _, v1, v2 = carta.split()  
        palo1, valor1 = v1.split("-")  
        iden = int(v2)  
        carta_tupla = (palo1, int(valor1))  
        
        manos[iden].remove(carta_tupla)
        cartas_jugadas[i] = carta_tupla
        puntuacion_cartas.append(carta_tupla)
        
    carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
    indice_ganador = puntuacion_cartas.index(carta_gandora)
    
    #Sumo puntos al jugador que ha ganado la baza
    if jugadores[indice_ganador] == jugadores_inicial[0]:
        puntosJugador0 += sumar_puntos(cartas_jugadas)
        await send_to_all_clients("Ganador: 0", players_connected)
    else:
        puntosJugador1 += sumar_puntos(cartas_jugadas)
        await send_to_all_clients("Ganador: 1", players_connected)
    #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
    if indice_ganador == 1:
        jugadores = jugadores[1:] + jugadores[:1]
                
    return jugadores, puntosJugador0, puntosJugador1, manos, indice_ganador

#Repartir carta robada a los jugadores
async def repartir(jugadores_inicial, mazo, triunfo, manos):
    for i, player_id in enumerate(jugadores_inicial):
        if len(mazo) == 0:
            carta_robada = triunfo
        else:
            carta_robada = mazo[0]
            mazo.remove(carta_robada)
        manos[i].append(carta_robada)
        mano_send = manos[i]
        message = json.dumps(mano_send)
        asyncio.create_task(send_to_single_client(player_id, message, players_connected))
        
    return mazo, manos

async def arrastre(websocket, jugadores_inicial, jugadores, players_connected, triunfo, puntosJugador0, puntosJugador1, manos):
    cartas_jugadas = (None, None)
    puntuacion_cartas = ()
    for i, player_id in enumerate(jugadores):
        indice = 0
        #si eres el primero en tirar puedes usar lo que quieras
        if i == 0:
            if jugadores[i] == jugadores_inicial[1]:
                indice = 1
            mano_send = {"0": cartas_jugadas[0], "1": cartas_jugadas[1] ,"Turno": indice, "Triunfo": None}
            message = json.dumps(mano_send)
            asyncio.create_task(send_to_all_clients(message, players_connected))
            print(manos[indice])
            mano_send = manos[indice]
            message = json.dumps(mano_send)
            asyncio.create_task(send_to_single_client(player_id, message, players_connected))
        else:
            if jugadores[i] == jugadores_inicial[1]:
                indice = 1
            mano_send = {"0": cartas_jugadas[0], "1": cartas_jugadas[1] ,"Turno": indice, "Triunfo": None}
            message = json.dumps(mano_send)
            asyncio.create_task(send_to_all_clients(message, players_connected))
            
            cartas_posibles = que_cartas_puede_usar_jugador_arrastre(manos[indice], puntuacion_cartas, triunfo)

            message = json.dumps(cartas_posibles)
            asyncio.create_task(send_to_single_client(player_id, message, players_connected))
        
        carta = await websocket.receive_text()
        
        if carta[0] !=  "A":
            break
        
        _, v1, v2 = carta.split()  
        palo1, valor1 = v1.split("-")  
        iden = int(v2)  
        carta_tupla = (palo1, int(valor1))  
        
        manos[iden].remove(carta_tupla)
        cartas_jugadas[i] = carta_tupla
        puntuacion_cartas.append(carta_tupla)
    print(puntuacion_cartas)    
    carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
    indice_ganador = puntuacion_cartas.index(carta_gandora)
    
    #Sumo puntos al jugador que ha ganado la baza
    if jugadores[indice_ganador] == jugadores_inicial[0]:
        puntosJugador0 += sumar_puntos(cartas_jugadas)
        await send_to_all_clients("Ganador: 0", players_connected)
    else:
        puntosJugador1 += sumar_puntos(cartas_jugadas)
        await send_to_all_clients("Ganador: 1", players_connected)
    #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
    if indice_ganador == 1:
        jugadores = jugadores[1:] + jugadores[:1]
    
    return jugadores, manos, puntosJugador0, puntosJugador1


async def send_to_all_clients(message: str, connected_clients: dict):
    for websocket in connected_clients.values():
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            pass
        
async def send_to_single_client(client_id: str, message: str, connected_clients: dict):
    websocket = connected_clients.get(client_id)
    
    if websocket is not None:
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            pass
    else:
        print(f"No se encontró el cliente con ID: {client_id}")
        

async def comprobarGanador(puntosJugador0, puntosJugador1):
    if puntosJugador1 >= 100:
        message = "Gana el jugador 0, Puntos0: " + str(puntosJugador0) + " , Puntos1: " + str(puntosJugador1)
        await send_to_all_clients(message, players_connected)
        return True
    elif puntosJugador1 >= 100:
        message = "Gana el jugador 1, Puntos0: " + str(puntosJugador0) + " , Puntos1: " + str(puntosJugador1)
        await send_to_all_clients(message, players_connected)
        return True
    else:
        return False




        
