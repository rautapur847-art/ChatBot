import flet as ft
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import threading
import time

SAMPLE_RATE = 16000
CHANNELS = 1

# Auto-stop tuning: after speech is detected, stop once the mic has been
# quiet for SILENCE_SECONDS. RMS_THRESHOLD is the loudness level (on a
# 16-bit scale) above which a chunk counts as "speech" rather than
# background noise - raise it if it's triggering on room noise, lower it
# if it's cutting you off too early.
RMS_THRESHOLD = 300
SILENCE_SECONDS = 1.2
MAX_RECORD_SECONDS = 15


class MicScreen:
    """
    Microphone recorder, structured the same way as CameraScreen:
    the caller (home.py) passes in callbacks instead of this class
    reaching into page.overlay to find widgets.

      - on_status(text, color): called to update a status message
      - on_result(text): called once speech has been transcribed
      - on_recording_change(is_recording): called when recording starts/stops,
        so the caller can swap the mic icon (e.g. mic <-> stop)

    Recording auto-stops (and transcribes) once you go quiet for a moment,
    so you don't have to tap the mic a second time - though a second tap
    still stops it manually if you want to end it early.

    Uses `sounddevice` (not `pyaudio`) to capture audio, since sounddevice
    ships prebuilt wheels for Windows and doesn't need a C++ compiler to
    install. The recorded audio is fed into SpeechRecognition's Google Web
    Speech API for transcription.
    """

    def __init__(self, page: ft.Page, on_status=None, on_result=None, on_recording_change=None):
        self.page = page
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.speech_started = False
        self.last_voice_time = 0.0

        self.on_status = on_status or (lambda text, color="white": None)
        self.on_result = on_result or (lambda text: None)
        self.on_recording_change = on_recording_change or (lambda is_recording: None)

    def toggle_mic(self, e):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.speech_started = False
        self.last_voice_time = time.time()
        self.on_recording_change(True)
        self.on_status("Listening... boliye, khamoshi hote hi auto-stop hoga.", "blue")

        def callback(indata, frame_count, time_info, status):
            # Runs on sounddevice's own audio thread.
            self.frames.append(indata.copy())
            rms = float(np.sqrt(np.mean(indata.astype(np.float64) ** 2)))
            if rms > RMS_THRESHOLD:
                self.speech_started = True
                self.last_voice_time = time.time()

        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                callback=callback,
            )
            self.stream.start()
            threading.Thread(target=self._watch_for_silence, daemon=True).start()
        except Exception as ex:
            self.is_recording = False
            self.on_recording_change(False)
            self.on_status(f"Microphone error: {ex}", "red")

    def _watch_for_silence(self):
        start_time = time.time()
        while self.is_recording:
            time.sleep(0.1)
            if not self.is_recording:
                return
            now = time.time()
            if self.speech_started and (now - self.last_voice_time) > SILENCE_SECONDS:
                self.stop_recording()
                return
            if (now - start_time) > MAX_RECORD_SECONDS:
                self.stop_recording()
                return

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.on_recording_change(False)

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.on_status("Transcribing...", "blue")
        # Transcription hits the network (Google's speech API), so run it
        # off the main thread.
        threading.Thread(target=self._transcribe, daemon=True).start()

    def _transcribe(self):
        if not self.frames or not self.speech_started:
            self.on_status("Kuch bola nahi gaya — dobara try karein.", "red")
            return
        try:
            audio_np = np.concatenate(self.frames, axis=0)
            audio_bytes = audio_np.tobytes()
            # sample_width=2 because dtype="int16" above is 2 bytes/sample.
            audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)

            # language="en-IN" works well for Indian English; swap to
            # "hi-IN" if you want Hindi speech recognized instead.
            text = self.recognizer.recognize_google(audio_data, language="en-IN")
            self.on_status("", "white")
            self.on_result(text)
        except sr.UnknownValueError:
            self.on_status("Samajh nahi aaya — dobara try karein.", "red")
        except sr.RequestError as ex:
            self.on_status(f"Speech service error: {ex}", "red")
        except Exception as ex:
            self.on_status(f"Error: {ex}", "red")