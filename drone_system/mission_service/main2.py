from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import asyncio
from aiokafka import AIOKafkaProducer
from sqlalchemy import select
from models import Drone, FleetManager
from path import AStar, Grid_Maker
from database import init_db, AsyncSessionLocal
from models_db import MissionLog, BillingRecord



app = FastAPI()
redis_client = redis.asyncio.Redis(host="redis", port=6379, db=0, decode_responses=True)
kafka_producer = None

fleet = FleetManager()

class connection(BaseModel):
    Droneid: int
    tarx: float
    tary: float

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

moving_grid = Grid_Maker(grid_order=400)
interm = AStar(moving_grid)

@app.on_event("startup")
async def start_background_simulation():
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
    try:
        await init_db()
        print("Aurora connected successfully.")
    except Exception as e:
        print(f"Aurora unavailable, skipping DB init: {repr(e)}")

@app.get("/")
def mission_health_check():
    return {"status": "Mission service is alive!"}


@app.post("/assign-mission")
async def assign_mission(request:connection):
    mission = {
    "event" : "mission_assigned",
    "id" : request.Droneid,
    "tarx" : request.tarx,
    "tary" : request.tary
    }
    mission_value = json.dumps(mission).encode("utf-8")
    iid = await fleet.load_drone_from_redis(request.Droneid, redis_client)
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
        eta = len(path) * 0.1
        sec = round(eta, 2)
        #Aurora logging
        async with AsyncSessionLocal() as session:
            async with session.begin():
                mission_log = MissionLog(
                    drone_id=request.Droneid,
                    customer_id="default_customer",
                    start_x=iid.x,
                    start_y=iid.y,
                    target_x=request.tarx,
                    target_y=request.tary,
                    distance=round(cost, 2),
                    battery_consumed=round(required_cost, 2),
                    eta_seconds=sec,
                    status="assigned"
                )
                session.add(mission_log)
                await session.flush()

                billing = BillingRecord(
                    customer_id="default_customer",
                    drone_id=request.Droneid,
                    mission_id=mission_log.id,
                    units_consumed=round(required_cost * 0.1, 4)
                )
                session.add(billing)
        return f"Mission Assignment Complete. it will take about {sec}sec."
    else:
        raise HTTPException(status_code=400, detail="Battery not sufficient.")
    

@app.get("/missions")
async def get_missions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MissionLog).order_by(MissionLog.created_at.desc()).limit(50)
        )
        missions = result.scalars().all()
        return [
            {
                "id": m.id,
                "drone_id": m.drone_id,
                "customer_id": m.customer_id,
                "start_x": m.start_x,
                "start_y": m.start_y,
                "target_x": m.target_x,
                "target_y": m.target_y,
                "distance": m.distance,
                "battery_consumed": m.battery_consumed,
                "eta_seconds": m.eta_seconds,
                "status": m.status,
                "created_at": str(m.created_at),
            }
            for m in missions
        ]
    
@app.get("/billing")
async def get_billing():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BillingRecord).order_by(BillingRecord.created_at.desc()).limit(50)
        )
        records = result.scalars().all()
        return [
            {
                "id": r.id,
                "customer_id": r.customer_id,
                "drone_id": r.drone_id,
                "mission_id": r.mission_id,
                "units_consumed": r.units_consumed,
                "created_at": str(r.created_at),
            }
            for r in records
        ]
    
@app.get("/predict-congestion")
async def predict_congestion():
    ffleet = FleetManager()
    lit = await redis_client.smembers("drone_id_set")
    if not lit:  return {"predictions": []}
    for s in lit:
        droen = await fleet.load_drone_from_redis(int(s), redis_client)
        if not droen:  continue
        ffleet.add_drone(droen)
    predicted_crash = ffleet.predict_congestion()
    
    return {"predictions": predicted_crash} 


@app.on_event("shutdown") 
async def stop_gracefully():
    await kafka_producer.stop()
    await redis_client.close()