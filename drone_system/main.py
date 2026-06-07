from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Drone, FleetManager
import json
import asyncio
import redis
import math
from path import AStar, Grid_Maker
from pydantic import BaseModel
from config import API_URL


fleet = FleetManager()
fleet.add_drone(Drone(id=1, x=3.5, y=8.4,target_x=89.8, target_y=100.2))
fleet.add_drone(Drone(id=2, x=6.3, y=2.7, target_x=45.8, target_y=19.2))
fleet.add_drone(Drone(id=3, x=3.6, y=4.4, target_x=79.8, target_y=187.2))

class connection(BaseModel):
    Droneid: int
    tarx: float
    tary: float

app = FastAPI()
redis_client = redis.asyncio.Redis(host="localhost", port=6379, db=0, decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

moving_grid = Grid_Maker(grid_order=400)
interm = AStar(moving_grid)

@app.on_event("startup")
async def start_baground_simulation():
    asyncio.create_task(simulate_fleet())

@app.websocket("/ws")
async def simple_task(ws: WebSocket):   
    await ws.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("fleet_telemetry")
    async for message in pubsub.listen():
        if message["type"] == "message":
            lst = message["data"]
            await ws.send_text(lst)
            await asyncio.sleep(0.1)

async def simulate_fleet():
    while True:
        proxima = fleet.check_proximity()
        if proxima:
            print(f"Warning these are risky situation {proxima}")
        for i in fleet.get_all_drone():
            if i.status != "Landed":
                if i.battery > 0:
                    print(i.battery)
                    simulate_movement(i)
                    curr_battery = i.battery - 0.125
                    fleet.update_drone(id=i.id, battery = curr_battery)
                else:
                    fleet.update_drone(id=i.id, status="Landed")
                    print("Battery critically low")
                    print(f"Landed at {i.x},{i.y}")
                    
        lst = []
        for i in fleet.get_all_drone():
            fleet_telemetry = {"id": i.id, "x": i.x, "y": i.y, "battery": i.battery, "status": i.status}
            lst.append(fleet_telemetry)

        await redis_client.publish("fleet_telemetry", json.dumps(lst))
        await asyncio.sleep(0.1)

def simulate_movement(drone):

    col = int(drone.x//0.5)
    row = int(drone.y//0.5)
    tar_col = int(drone.target_x//0.5)
    tar_row = int(drone.target_y//0.5)
    if not drone.intermediate_steps:
        drone.intermediate_steps = interm.find_path((col, row), (tar_col, tar_row))[0]
    dx = drone.target_x-drone.x
    dy = drone.target_y-drone.y
    dist = math.sqrt(dx**2 + dy**2)


    if drone.battery > 0:
        if drone.status != "Landed":
            if dist > 0.5:
                if any(moving_grid.available_cell(*n) == 0 for n in drone.intermediate_steps):
                    drone.intermediate_steps= interm.find_path((col, row), (tar_col, tar_row))[0]

                else:
                    stepsx, stepsy = drone.intermediate_steps.pop(0)
                    stx = stepsx*0.5
                    sty = stepsy*0.5
                    fleet.update_drone(id=drone.id, x=stx, y=sty, status="On Air")
                    print(f"drone{drone.id} at {stepsx},{stepsy}")
                    if drone.battery <= 20 :
                        print("critical")

            else:
                fleet.update_drone(id=drone.id, x = drone.target_x, y = drone.target_y, status = "Landed")
                return f"Landed at {drone.x},{drone.y}"
            
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

@app.get("/{col}/{row}")
def get_obstacle_info(col:int, row:int):
    moving_grid.obstacle(col, row)

@app.post("/assign-mission")
async def assign_mission(request:connection):
    
    iid = fleet.get_drone(request.Droneid)
    # Option 1 - check the type
    if not isinstance(iid, Drone):
        raise HTTPException(status_code=404, detail="Drone not found.")
    # Option 2 - check if it's a Drone instance

    col = int(iid.x//0.5)
    row = int(iid.y//0.5)
    tar_coll = int(request.tarx//0.5)
    tar_roww = int(request.tary//0.5) 
    path, cost= interm.find_path((col, row), (tar_coll, tar_roww))
    estimated_cost = cost*0.25
    required_cost = estimated_cost*1.20
    if iid.battery >= required_cost:
        fleet.update_drone(iid.id, tarx=request.tarx, tary=request.tary, status="idle")
        iid.intermediate_steps.clear()
        eta = len(path) * 0.1
        return f"Mission Assignment Complete. it will take {eta}sec."
    else:
        raise HTTPException(status_code=400, detail="Battery not sufficient.")
    
