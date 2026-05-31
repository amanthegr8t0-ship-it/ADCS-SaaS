from dataclasses import dataclass
import math
from config import MIN_DISTANCE

@dataclass
class Drone:
    id: int 
    x:float = 0.0
    y:float = 0.0
    battery:float = 100.0
    status:str = "idle"
    heading:float = 0.0
    target_x:float = 0.0
    target_y:float = 0.0

class FleetManager():
    def __init__(self):
        self.fleet = {}

    def get_drone(self, id):
        return self.fleet.get(id, {"Detail": f"Drone with {id} dosen't exist."})

    def get_all_drone(self):
        drone_list = []
        for i in self.fleet:
            drone_list.append(self.fleet[i])

        if not drone_list:
            return {"Detail": "NO Drone exists in the fleet."}
        else:
            return drone_list
            

    def add_drone(self, drone):
        self.fleet[drone.id] = drone
        return {"Detail": f"Drone added to the fleet"}

    def update_drone(self, id, status = None, battery = None, tarx = None, tary = None, x = None, y = None):
        drone=self.fleet.get(id)
        if drone is not None:
            if status is not None:
                drone.status = status
            if battery is not None:
                drone.battery = battery
            if tarx is not None:
                drone.target_x = tarx
            if tary is not None:
                drone.target_y = tary
            if x is not None:
                drone.x = x
            if y is not None:
                drone.y = y
            return {"Detail": f"Updated Drone with id {id}"}
        return {"Detail": f"Drone with {id} dosen't exist."}
    
    def check_proximity(self) -> list[tuple]:
        drones = list(self.fleet.values()) 

        collision_list = []
        # collided = []
        for i in range(len(drones)):
            for j in range(i+1,len(drones)):
                stat1, stat2 = drones[i].status, drones[j].status
                dist = math.sqrt((drones[i].x-drones[j].x)**2 + (drones[i].y-drones[j].y)**2)
                if dist == 0 and stat1 != "Landed" and stat2 != "Landed":
                    collision_list.append((drones[i].id, drones[j].id))
                elif dist <= MIN_DISTANCE and stat1 != "Landed" and stat2 != "Landed" :
                    
                    collision_list.append((drones[i].id, drones[j].id))
        return collision_list
            

if __name__ == "__main__":
    drone_1 = Drone(id=23, x=2.3, y=2.4, battery=53.0)
    print(drone_1)