from dataclasses import dataclass

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

if __name__ == "__main__":
    drone_1 = Drone(id=23, x=2.3, y=2.4, battery=53.0)
    print(drone_1)