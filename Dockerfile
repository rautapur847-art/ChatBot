# Pinned to Debian 12 "bookworm" (stable) instead of the unpinned
# "slim" tag, which currently resolves to Debian 13 "trixie" — a very
# new/testing release where package names keep changing (that's exactly
# why libgl1-mesa-glx disappeared). Bookworm is stable and won't shift
# under you the way "slim" (unpinned) can.
FROM python:3.11-slim-bookworm

WORKDIR /app

# System packages needed to build/run this project's dependencies:
#   - portaudio19-dev: required to build sounddevice/pyaudio-style audio
#     bindings (used by mic.py)
#   - gcc, python3-dev: needed to compile C extensions some packages rely
#     on (e.g. mysql-connector-python, cryptography)
#
# Note: we do NOT install libgl1-mesa-glx / libglvnd0 here at all — see
# the requirements.txt note below on switching to opencv-python-headless,
# which removes the GUI/OpenGL dependency chain entirely instead of
# chasing whatever Debian happens to call it this week.
RUN apt-get update && apt-get install -y --no-install-recommends \
        portaudio19-dev \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "main.py"]
