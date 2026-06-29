MIN_DISTANCE = 10 #Least distance before landing 
API_URL = "http://localhost:8000"
DANGER_DISTANCE = 50 # Distance after which congestion check will be there
CONGESTION_DISTANCE = 2
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:yourpassword@localhost:5432/adcs")