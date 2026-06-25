from fastapi import FastAPI, HTTPException
import redis
from models import Drone, FleetManager
from path import AStar, Grid_Maker
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import json
import math

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.asyncio.Redis(host="redis", port=6379, db=0, decode_responses=True)
kafka_producer = None
moving_grid = Grid_Maker(grid_order=400)
interm = AStar(moving_grid)
logger = logging.getLogger(__name__)
fleet = FleetManager()

# Drone initialization
fleet.add_drone(Drone(id=1, x=3.5, y=8.4, status="idle"))
fleet.add_drone(Drone(id=2, x=6.3, y=2.7, status="idle"))
fleet.add_drone(Drone(id=3, x=3.6, y=4.4, status="idle"))

@app.on_event("startup")
async def start_background_simulation():
    await redis_client.sadd("drone_id_set", 1, 2, 3)
    global kafka_producer
    kafka_producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")
    connected = False
    while not connected:
        try:
            await kafka_producer.start()
            connected = True
            print("Successfully connected to Kafka!")
        except Exception as e:
            print(f"Kafka not ready yet, retrying in 3 seconds... Error: {e}")
            await asyncio.sleep(3)
    asyncio.create_task(simulate_fleet())
    asyncio.create_task(consume_missions())

async def simulate_fleet():
    while True:
        proxima = fleet.check_proximity()
        congestion_risk = fleet.predict_congestion()
        if proxima:
            print(f"Warning these are risky situation {proxima}")
        if congestion_risk:
            conflicting_path_dict = {}
            # future_path = []
            for i in congestion_risk:
                if i["id1"] > i["id2"]:
                    conflicting_path_dict.setdefault(i["id1"], []).append(i["path_of_drone_2"])
            for i in conflicting_path_dict:
                path_to_be_changed = i
                drone = fleet.get_drone(path_to_be_changed)
                col = int(drone.x//0.5)
                row = int(drone.y//0.5)
                tar_col = int(drone.target_x//0.5)
                tar_row = int(drone.target_y//0.5)
                for a in conflicting_path_dict[i]:
                    for b in a:
                        moving_grid.obstacle(*b)
                drone.intermediate_steps = interm.find_path((col, row), (tar_col, tar_row))[0]
                for a in conflicting_path_dict[i]:
                    for b in a:
                        moving_grid.mark_available(*b)
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

async def consume_missions():
    kafka_consumer = AIOKafkaConsumer("drone-missions", bootstrap_servers="kafka:9092")
    await kafka_consumer.start()
    try:
        async for message in kafka_consumer:
            data = json.loads(message.value)
            if data["event"] == "mission_assigned":
                fleet.update_drone(id=data["id"], tarx=data["tarx"], tary=data["tary"], status="On Air")
                drone = fleet.get_drone(data["id"])
                drone.intermediate_steps.clear()
    except Exception as e:
        logger.warning(f"mission assignment failed. {e}")
    finally:
        await kafka_consumer.stop()
    

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
    

@app.on_event("shutdown")
async def stop_gracefully():
    await kafka_producer.stop()
    await redis_client.close()