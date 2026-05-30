from fastapi import FastAPI, HTTPException, websocket
from drone_system.models import Drone
import asyncio
from datetime import datetime

fleet = {1 : Drone(id=1, x=3.5, y=8.4), 2 : Drone(id=8, x=6.3, y=2.7), 3 : Drone(id=3, x=3.6, y=4.4)}
app = FastAPI()

# @app.on_event("startup")
# async def 

def stimulate_fleet():
    for i,j in fleet.values():
        print (i.battery, j.battery)

# b = stimulate_fleet()
# print(fleet[1])


@app.websocket("/ws")
async def simple_task(ws: websocket):
    await ws.accept()
    while True:
        await ws.send_text(str(datetime.now()))
        await asyncio.sleep(2)

c = simple_task()
print(c)