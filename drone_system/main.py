from fastapi import FastAPI, HTTPException, WebSocket
from models import Drone, FleetManager
import json
import asyncio
import math

fleet = FleetManager()
fleet.add_drone(Drone(id=1, x=3.5, y=8.4,target_x=89.8, target_y=100.2))
fleet.add_drone(Drone(id=2, x=6.3, y=2.7, target_x=45.8, target_y=19.2))
fleet.add_drone(Drone(id=3, x=3.6, y=4.4, target_x=79.8, target_y=187.2))
app = FastAPI()

@app.on_event("startup")
async def start_baground_simulation():
    asyncio.create_task(simulate_fleet())

@app.websocket("/ws")
async def simple_task(ws: WebSocket):
    await ws.accept()
    while True:
        lst = []
        for i in fleet.get_all_drone():
            fleet_telemetry = {"id": i.id, "x": i.x, "y": i.y, "battery": i.battery, "status": i.status}
            lst.append(fleet_telemetry)
        await ws.send_text(json.dumps(lst))
        await asyncio.sleep(1)

async def simulate_fleet():
    while True:
        proxima = fleet.check_proximity()
        if proxima:
            print(f"Warning these are risky situation {proxima}")
        for i in fleet.get_all_drone():
            if i.battery > 0:
                print(i.battery)
                simulate_movement(i)
                curr_battery = i.battery - 0.5
                fleet.update_drone(id=i.id, battery = curr_battery)
            else:
                fleet.update_drone(id=i.id, status="Landed")
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
            xpos = drone.x + (dx/dist)*step_size
            ypos = drone.y + (dy/dist)*step_size
            fleet.update_drone(id=drone.id, x=xpos, y=ypos)
            print(f"drone at {xpos},{ypos}")
            if drone.battery <= 20 :
                print("critical")

        else:
            fleet.update_drone(id=drone.id, x = drone.target_x, y = drone.target_y, status = "Landed")
            return f"Landed at {drone.x},{drone.y}"
        
    else:
        fleet.update_drone(id=drone.id, status = "Landed")
        return f"Landed at {drone.x},{drone.y}"

@app.get("/")
def get_fleet_status():
    return {"status":"all drone are fine"}

@app.get("/drone/{drone_id}")
def get_drone_telemetry(drone_id : int):
    
    return fleet.get_drone(drone_id)
    
        # raise HTTPException(status_code=404, detail="Drone not found")
        