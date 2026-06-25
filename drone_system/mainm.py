from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models import Drone, FleetManager
import json
import asyncio
import redis
import math
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, TopicPartition
import logging
from path import AStar, Grid_Maker
from pydantic import BaseModel 
from config import API_URL
import time

# Record exactly when the server started
SERVER_START_TIME_MS = int(time.time() * 1000)


logger = logging.getLogger(__name__)
fleet = FleetManager()
fleet.add_drone(Drone(id=1, x=3.5, y=8.4, status="idle"))
fleet.add_drone(Drone(id=2, x=6.3, y=2.7, status="idle"))
fleet.add_drone(Drone(id=3, x=3.6, y=4.4, status="idle"))

class connection(BaseModel): 
    Droneid: int
    tarx: float
    tary: float

app = FastAPI()
redis_client = redis.asyncio.Redis(host="localhost", port=6379, db=0, decode_responses=True)
kafka_producer = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

moving_grid = Grid_Maker(grid_order=400)
interm = AStar(moving_grid)

@app.get("/server-info")
def get_server_info():
    return {"start_time": SERVER_START_TIME_MS}

@app.on_event("startup")
async def start_baground_simulation():
    asyncio.create_task(simulate_fleet())
    global kafka_producer
    kafka_producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await kafka_producer.start()

@app.websocket("/ws")
async def simple_task(ws: WebSocket):   
    await ws.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("fleet_telemetry")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                lst = message["data"]
                await ws.send_text(lst)
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        # Client swapped tabs or disconnected cleanly
        print("Frontend disconnected from live telemetry.")
    finally:
        await pubsub.unsubscribe("fleet_telemetry")


async def simulate_fleet():
    while True:
        proxima = fleet.check_proximity()
        if proxima:
            print(f"Warning these are risky situation {proxima}")
        for i in fleet.get_all_drone():
            if i.status == "On Air":
                if i.battery > 0:
                    print(i.battery)
                    mission_event = await simulate_movement(i)
                    if mission_event: 
                        event_payload = json.dumps(mission_event).encode("utf-8")
                        await kafka_producer.send("drone-missions", value=event_payload)
                else:
                    fleet.update_drone(id=i.id, status="Landed")
                    print("Battery critically low")
                    print(f"Landed at {i.x},{i.y}")
                    
        lst = [] 
        for i in fleet.get_all_drone():
            fleet_telemetry = {"id": i.id, "x": i.x, "y": i.y, "battery": i.battery, "status": i.status}
            
            lst.append(fleet_telemetry) 
            await fleet.save_drone_to_redis(i, redis_client)
        try:
            await kafka_producer.send("drone-telemetry", value=json.dumps(lst).encode("utf-8"))
            await redis_client.publish("fleet_telemetry", json.dumps(lst))
        except Exception as e:
            print(f"Telemetry broadcast failed: {e}") 
        await asyncio.sleep(0.1) 

async def simulate_movement(drone):

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
        if drone.status == "On Air":
            if dist > 0.5:
                if not drone.intermediate_steps and (col, row) != (tar_col, tar_row):
                    fleet.update_drone(drone.id, status="Landed")
                    logger.warning("No path ahead and drone is not at the destination.")
                    return
                    
                if any(moving_grid.available_cell(*n) == 0 for n in drone.intermediate_steps):
                    drone.intermediate_steps= interm.find_path((col, row), (tar_col, tar_row))[0]

                else:
                    stepsx, stepsy = drone.intermediate_steps.pop(0)
                    stx = stepsx*0.5
                    sty = stepsy*0.5
                    curr_battery = drone.battery - 0.125
                    fleet.update_drone(id=drone.id, x=stx, y=sty, status="On Air", battery=curr_battery)
                    print(f"drone{drone.id} at {stepsx},{stepsy}")
                    if drone.battery <= 20 :
                        print("critical")

            else:
                fleet.update_drone(id=drone.id, x = drone.target_x, y = drone.target_y, status = "Landed")
                # RETURN A STRUCTURED EVENT
                return {
                    "event": "mission_completed",
                    "drone_id": drone.id,
                    "x": drone.target_x,
                    "y": drone.target_y
                }
            
        else:
            return
            
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
    mission = {
    "event" : "mission_assigned",
    "id" : request.Droneid,
    "tarx" : request.tarx,
    "tary" : request.tary
    }
    mission_value = json.dumps(mission).encode("utf-8")
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
        await kafka_producer.send("drone-missions", value=mission_value)
        fleet.update_drone(iid.id, tarx=request.tarx, tary=request.tary, status="On Air")
        iid.intermediate_steps.clear()
        eta = len(path) * 0.1
        sec = round(eta, 2)
        return f"Mission Assignment Complete. it will take about {sec}sec."
    else:
        raise HTTPException(status_code=400, detail="Battery not sufficient.")
    
@app.websocket("/ws/replay")
async def replay(topic: str, ws: WebSocket, start_time_ms: int):
    try:
        kafka_consumer = AIOKafkaConsumer(bootstrap_servers="localhost:9092")
        await ws.accept()
        await kafka_consumer.start()
        tp = TopicPartition(topic, 0)
        kafka_consumer.assign([tp])
        offset_no = await kafka_consumer.offsets_for_times({tp: start_time_ms})
        timerecord = offset_no[tp]
        
        if timerecord is not None:
            offset = timerecord.offset
            kafka_consumer.seek(tp, offset)
        else:
            # The requested time is in the future. Don't crash, just seek to the end.
            await kafka_consumer.seek_to_end(tp)
        
        async for messages in kafka_consumer:
            message = messages.value
            await ws.send_text(message.decode("utf-8"))
            await asyncio.sleep(0.1)
    except Exception as e:
        await ws.close(code=1011, reason=str(e))

    finally:
        await kafka_consumer.stop()

@app.get("/predict-congestion")
async def congestion_predictor():
    return fleet.predict_congestion()

@app.on_event("shutdown")
async def stop_gracefully():
    await kafka_producer.stop()
    await redis_client.close()
    print("Bye-Bye")