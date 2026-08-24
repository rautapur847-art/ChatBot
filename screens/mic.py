import flet as ft
import numpy as np
import speech_recognition as sr
import threading
import time
import asyncio
import flet_audio_recorder as far


# =========================================================
# SETTINGS
# =========================================================

SAMPLE_RATE = 16000
CHANNELS = 1

RMS_THRESHOLD = 300
SILENCE_SECONDS = 1.2
MAX_RECORD_SECONDS = 15

BYTES_PER_SAMPLE = 2


# =========================================================
# MIC SCREEN
# =========================================================

class MicScreen:

    def __init__(
        self,
        page: ft.Page,
        on_status=None,
        on_result=None,
        on_recording_change=None,
    ):

        self.page = page

        self.recognizer = sr.Recognizer()

        # Recording state
        self.is_recording = False

        self.speech_started = False

        self.last_voice_time = 0.0

        self.record_start_time = 0.0

        # Audio chunks
        self.frames = bytearray()

        # Lock prevents race condition
        self.lock = threading.Lock()

        # Prevent multiple stop calls
        self.stop_lock = threading.Lock()

        # Audio recorder
        self.recorder = far.AudioRecorder(
            configuration=far.AudioRecorderConfiguration(
                encoder=far.AudioEncoder.PCM16BITS,
                sample_rate=SAMPLE_RATE,
                channels=CHANNELS,
            ),
            on_stream=self._on_audio_stream,
            on_state_change=self._on_state_change,
        )

        # Callbacks
        self.on_status = (
            on_status
            or (lambda text, color="white": None)
        )

        self.on_result = (
            on_result
            or (lambda text: None)
        )

        self.on_recording_change = (
            on_recording_change
            or (lambda is_recording: None)
        )


    # =====================================================
    # AUDIO STREAM CALLBACK
    # =====================================================

    def _on_audio_stream(self, e):

        if not self.is_recording:
            return

        try:

            chunk = e.chunk

            if not chunk:
                return

            # Save audio safely
            with self.lock:

                if not self.is_recording:
                    return

                self.frames.extend(chunk)

            # ---------------------------------------------
            # Calculate RMS for silence detection
            # ---------------------------------------------

            audio_np = np.frombuffer(
                chunk,
                dtype=np.int16
            )

            if len(audio_np) == 0:
                return

            rms = float(
                np.sqrt(
                    np.mean(
                        audio_np.astype(
                            np.float64
                        ) ** 2
                    )
                )
            )

            # Speech detected
            if rms > RMS_THRESHOLD:

                self.speech_started = True

                self.last_voice_time = time.time()

        except Exception as ex:

            print(
                f"Audio stream error: {ex}"
            )


    # =====================================================
    # AUDIO RECORDER STATE
    # =====================================================

    def _on_state_change(self, e):

        print(
            f"Audio recorder state: {e.data}"
        )


    # =====================================================
    # TOGGLE MIC
    # =====================================================

    async def toggle_mic(self, e):

        try:

            if self.is_recording:

                await self.stop_recording()

            else:

                await self.start_recording()

        except Exception as ex:

            print(
                f"Toggle microphone error: {ex}"
            )

            self.on_status(
                f"Microphone error: {ex}",
                "red"
            )


    # =====================================================
    # START RECORDING
    # =====================================================

    async def start_recording(self):

        # Prevent duplicate start
        if self.is_recording:

            return


        try:

            # ---------------------------------------------
            # Ask microphone permission
            # ---------------------------------------------

            permission = await self.recorder.has_permission()

            if not permission:

                self.on_status(
                    "Microphone permission denied.",
                    "red"
                )

                return


            # ---------------------------------------------
            # Reset state
            # ---------------------------------------------

            with self.lock:

                self.frames = bytearray()

            self.speech_started = False

            self.last_voice_time = time.time()

            self.record_start_time = time.time()

            self.is_recording = True


            self.on_recording_change(True)

            self.on_status(
                "Listening... boliye, khamoshi hote hi auto-stop hoga.",
                "blue"
            )


            # ---------------------------------------------
            # Start browser/device microphone
            # ---------------------------------------------

            started = await self.recorder.start_recording(
                configuration=far.AudioRecorderConfiguration(
                    encoder=far.AudioEncoder.PCM16BITS,
                    sample_rate=SAMPLE_RATE,
                    channels=CHANNELS,
                )
            )


            if not started:

                self.is_recording = False

                self.on_recording_change(False)

                self.on_status(
                    "Microphone start nahi ho paya.",
                    "red"
                )

                return


            # ---------------------------------------------
            # Start silence watcher
            # ---------------------------------------------

            asyncio.create_task(
                self._watch_for_silence()
            )

        except Exception as ex:

            self.is_recording = False

            self.on_recording_change(False)

            self.on_status(
                f"Microphone error: {ex}",
                "red"
            )


    # =====================================================
    # WATCH SILENCE
    # =====================================================

    async def _watch_for_silence(self):

        while self.is_recording:

            await asyncio.sleep(0.1)

            if not self.is_recording:

                return


            now = time.time()


            # ---------------------------------------------
            # Auto stop after silence
            # ---------------------------------------------

            if (
                self.speech_started
                and
                (
                    now - self.last_voice_time
                    > SILENCE_SECONDS
                )
            ):

                await self.stop_recording()

                return


            # ---------------------------------------------
            # Maximum recording time
            # ---------------------------------------------

            if (
                now - self.record_start_time
                > MAX_RECORD_SECONDS
            ):

                await self.stop_recording()

                return


    # =====================================================
    # STOP RECORDING
    # =====================================================

    async def stop_recording(self):

        # ---------------------------------------------
        # Prevent double stop
        # ---------------------------------------------

        with self.stop_lock:

            if not self.is_recording:

                return

            self.is_recording = False


        self.on_recording_change(False)


        # ---------------------------------------------
        # Stop browser/device recorder
        # ---------------------------------------------

        try:

            await self.recorder.stop_recording()

        except Exception as ex:

            print(
                f"Audio recorder stop error: {ex}"
            )


        # ---------------------------------------------
        # Take safe snapshot
        # ---------------------------------------------

        with self.lock:

            audio_bytes = bytes(
                self.frames
            )

            self.frames = bytearray()


        speech_started = self.speech_started

        self.speech_started = False


        # ---------------------------------------------
        # Check recording
        # ---------------------------------------------

        if (
            not audio_bytes
            or
            not speech_started
        ):

            self.on_status(
                "Kuch bola nahi gaya — dobara try karein.",
                "red"
            )

            return


        # ---------------------------------------------
        # Transcribing
        # ---------------------------------------------

        self.on_status(
            "Transcribing...",
            "blue"
        )


        # ---------------------------------------------
        # Background transcription
        # ---------------------------------------------

        threading.Thread(
            target=self._transcribe,
            args=(audio_bytes,),
            daemon=True,
        ).start()


    # =====================================================
    # TRANSCRIBE
    # =====================================================

    def _transcribe(self, audio_bytes):

        try:

            # -----------------------------------------
            # Create SpeechRecognition AudioData
            # -----------------------------------------

            audio_data = sr.AudioData(
                audio_bytes,
                SAMPLE_RATE,
                BYTES_PER_SAMPLE,
            )


            # -----------------------------------------
            # Google Speech Recognition
            # -----------------------------------------

            text = self.recognizer.recognize_google(
                audio_data,
                language="en-IN"
            )


            # -----------------------------------------
            # Result
            # -----------------------------------------

            self.on_status(
                "",
                "white"
            )

            self.on_result(
                text
            )


        # =============================================
        # Speech not understood
        # =============================================

        except sr.UnknownValueError:

            self.on_status(
                "Samajh nahi aaya — dobara try karein.",
                "red"
            )


        # =============================================
        # Google speech service error
        # =============================================

        except sr.RequestError as ex:

            self.on_status(
                f"Speech service error: {ex}",
                "red"
            )


        # =============================================
        # Other errors
        # =============================================

        except Exception as ex:

            self.on_status(
                f"Error: {ex}",
                "red"
                )
