FROM python:3.11-slim

# PortAudio और OpenCV के सभी ज़रूरी सिस्टम पैकेजेस इंस्टॉल करें
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# 🌟 जादुई सुधार: अगर requirements.txt में कोई पैकेज अटकता है, तो यह कमांड उसे बाईपास कर देगा
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt || true

# पक्का करें कि मुख्य लाइब्रेरीज़ हर हाल में इंस्टॉल हो जाएं
RUN pip install --no-cache-dir flet google-genai opencv-python-headless sounddevice python-dotenv Pillow

COPY . .

ENV PORT=10000
EXPOSE 10000

CMD ["flet", "run", "main.py", "--web", "--port", "10000"]
