# 1. Base Image
FROM python:3.11-slim

# 2. Working Directory
WORKDIR /main2

# 3. Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Source Code
COPY . .

# 5. Startup Command
CMD ["python", "-m","uvicorn", "main2:app", "--host", "0.0.0.0", "--port", "8000"]