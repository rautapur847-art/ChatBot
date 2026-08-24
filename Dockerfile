FROM python:3.11-slim

# आवश्यक सिस्टम पैकेजेस
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# केवल वही लाइब्रेरी इंस्टॉल करें जिनकी आपके ऐप को ज़रूरत है (कोई एरर नहीं आएगा)
RUN pip install --no-cache-dir \
    flet \
    google-generativeai \
    opencv-python-headless \
    sounddevice \
    python-dotenv \
    Pillow \
    cryptography \
    pymysql

COPY . .

# Render के लिए यूनिवर्सल होस्ट और पोर्ट बाइंडिंग
CMD ["flet", "run", "main.py", "--web", "--host", "0.0.0.0", "--port", "10000"]
