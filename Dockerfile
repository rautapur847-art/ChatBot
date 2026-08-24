FROM python:3.11-slim

# PortAudio और अन्य ज़रूरी सिस्टम पैकेजेस इंस्टॉल करें
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render के लिए पोर्ट सेट करें
ENV PORT=8080
EXPOSE 8080

CMD ["flet", "run", "main.py", "--web", "--port", "8080"]
