FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first so Docker can reuse this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code.
COPY . .

# The application listens on port 8000 inside the container.
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
