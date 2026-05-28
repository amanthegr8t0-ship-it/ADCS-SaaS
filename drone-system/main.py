from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get_fleet_status():
    return {"status":"all drone are fine"}

@app.get("/drone/{drone_id}")
def get_drone_telemetry(drone_id : int):
    drone_cluster = {1 : {"bat" :"89", "x":67890, "y":56789, "temp" : "25c" }}
    return drone_cluster[drone_id]
        