from fastapi import FastAPI, HTTPException, WebSocket
from models import Drone
import json
import asyncio
import math

fleet = {1 : Drone(id=1, x=3.5, y=8.4,target_x=89.8, target_y=100.2), 2 : Drone(id=2, x=6.3, y=2.7, target_x=45.8, target_y=19.2), 3 : Drone(id=3, x=3.6, y=4.4, target_x=79.8, target_y=187.2)}
app = FastAPI()

@app.on_event("startup")
async def start_baground_simulation():
    asyncio.create_task(simulate_fleet())

@app.websocket("/ws")
async def simple_task(ws: WebSocket):
    await ws.accept()
    while True:
        lst = []
        for i in fleet.values():
            fleet_telemetry = {"id": i.id, "x": i.x, "y": i.y, "battery": i.battery, "status": i.status}
            lst.append(fleet_telemetry)
        await ws.send_text(json.dumps(lst))
        await asyncio.sleep(2)

async def simulate_fleet():
    while True:
        for i in fleet.values():
            if i.battery > 0: 
                print(i.battery)
                simulate_movement(i)
                i.battery -= 0.5
            else:
                print("Battery critically low")
                print(f"Landed at {i.x},{i.y}")
        await asyncio.sleep(1)

def simulate_movement(drone):
    step_size = 0.5
    
    dx = drone.target_x-drone.x
    dy = drone.target_y-drone.y
    dist = math.sqrt(dx**2 + dy**2)
    if drone.battery > 0:
        if dist > 0.5:
            drone.x += (dx/dist)*step_size
            drone.y += (dy/dist)*step_size
            print(f"drone at {drone.x},{drone.y}")
            if drone.battery <= 20 :
                print("critical")

        else:
            drone.x, drone.y = drone.target_x, drone.target_y
            drone.status = "Landed"
            return f"Landed at {drone.x},{drone.y}"

    else:
        drone.status = "Landed"
        return f"Landed at {drone.x},{drone.y}"

@app.get("/")
def get_fleet_status():
    return {"status":"all drone are fine"}

@app.get("/drone/{drone_id}")
def get_drone_telemetry(drone_id : int):
    if drone_id in fleet:
        return fleet[drone_id]
    else:
        raise HTTPException(status_code=404, detail="Drone not found")
        