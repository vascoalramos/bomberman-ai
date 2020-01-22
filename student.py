import sys
import json
import asyncio
import websockets
import getpass
import os
import logging
import random

from mapa import Map

from bomberman import Bomberman

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Student")
logger.setLevel(logging.INFO)


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # you can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        # init bomberman agent properties
        bomberman = Bomberman()

        logger.debug("STARTING GAME")

        while True:
            try:
                while websocket.messages:
                    await websocket.recv()

                logger.debug(f"Websocket messages: {websocket.messages}")

                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                if "lives" not in state or not state["lives"]:
                    logger.debug("GAME OVER!")
                    return

                mapa.walls = state["walls"]

                # update our bomberman state
                bomberman.update_state(state, mapa)

                # choose next move of bomberman
                key = bomberman.next_move()

                if key is None:
                    logger.debug("RANDOM KEY")
                    moves = ["w", "a", "s", "d"]
                    key = random.choice(moves)

                logger.debug(f"P: {bomberman.pos} | K: {key}")

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
