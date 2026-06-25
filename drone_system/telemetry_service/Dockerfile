# 1. Base Image
FROM python:3.11-slim

# 2. Working Directory
WORKDIR /main1

# 3. Dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# 4. Source Code
COPY . .

# 5. Startup Command
CMD ["python", "-m","uvicorn", "main1:app", "--host", "0.0.0.0", "--port", "8000"]