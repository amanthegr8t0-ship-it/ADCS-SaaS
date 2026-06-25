import asyncio 
from models import FleetManager 
from aiokafka import AIOKafkaConsumer, TopicPartition 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse 
from fastapi.middleware.cors import CORSMiddleware
import redis 
import time 
import httpx 
from pydantic import BaseModel 


fleet = FleetManager()
app = FastAPI()
redis_client = redis.asyncio.Redis(host="redis", port=6379, db=0, decode_responses=True) 
SERVER_START_TIME_MS = int(time.time() * 1000)

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

@app.get("/server-info")
def get_server_info():
    return {"start_time": SERVER_START_TIME_MS}

@app.get("/")
def get_fleet_status():
    return {"status":"all drone are fine"}

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


@app.post("/assign-mission")
async def assign_mission(request: connection): 
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mission-service:8000/assign-mission", 
            json=request.model_dump()
        )
        return JSONResponse (status_code=response.status_code,
            content=response.json())

@app.get("/drone/{drone_id}")
async def get_drone_telemetry(drone_id : int):
    return await fleet.load_drone_from_redis(drone_id, redis_client)  

@app.websocket("/ws/replay")
async def replay(topic: str, ws: WebSocket, start_time_ms: int):
    try:
        kafka_consumer = AIOKafkaConsumer(bootstrap_servers="kafka:9092")
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

@app.on_event("shutdown")
async def stop_gracefully():
    await redis_client.close()