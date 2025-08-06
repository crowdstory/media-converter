FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# CMD [\"python3\", \"examples/demo.py\"]
CMD ["sh", "-c", "tail -f /dev/null"]

