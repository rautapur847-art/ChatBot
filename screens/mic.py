import flet as ft
import flet_audio_recorder as far
import speech_recognition as sr
import asyncio
import threading
import time
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2

# Kitni der silence hone par mic automatically stop hoga
SILENCE_SECONDS = 1.2

# Maximum recording time
MAX_RECORD_SECONDS = 30

# Speech detection
RMS_THRESHOLD = 350

# Har kitne seconds ke audio ko transcription ke liye bhejna hai
TRANSCRIBE_INTERVAL = 1.5


class MicScreen:

    def __init__(
        self,
        page: ft.Page,
        on_status=None,
        on_result=None,
        on_recording_change=None,
    ):

        self.page = page

        # ----------------------------------------------------
        # Callbacks
        # ----------------------------------------------------

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
            or (lambda recording: None)
        )

        # ----------------------------------------------------
        # Speech recognizer
        # ----------------------------------------------------

        self.recognizer = sr.Recognizer()

        # ----------------------------------------------------
        # Audio recorder
        # ----------------------------------------------------

        self.recorder = far.AudioRecorder(
            on_stream=self._on_audio_stream,
            on_state_change=self._on_state_change,
        )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.is_recording = False

        self.speech_started = False

        self.last_voice_time = 0.0

        self.record_start_time = 0.0

        # All received PCM audio
        self.audio_buffer = bytearray()

        # Audio waiting for transcription
        self.transcription_buffer = bytearray()

        # Final text
        self.final_text = ""

        # Prevent multiple transcription jobs
        self.transcribing = False

        # Prevent multiple stop calls
        self.stop_in_progress = False

        # Lock for audio buffers
        self.lock = threading.Lock()

        # Last transcription time
        self.last_transcription_time = 0.0

        # Async watcher task
        self.watch_task = None


    # ============================================================
    # MIC BUTTON
    # ============================================================

    def toggle_mic(self, e):

        # Flet event handler can launch coroutine
        self.page.run_task(
            self._toggle_mic
        )


    async def _toggle_mic(self):

        try:

            if self.is_recording:

                await self.stop_recording()

            else:

                await self.start_recording()

        except Exception as ex:

            print(
                "Mic toggle error:",
                ex
            )

            self.on_status(
                f"Microphone error: {ex}",
                "red"
            )


    # ============================================================
    # START RECORDING
    # ============================================================

    async def start_recording(self):

        if self.is_recording:

            return

        if self.stop_in_progress:

            return

        try:

            # ------------------------------------------------
            # Microphone permission
            # ------------------------------------------------

            permission = (
                await self.recorder.has_permission()
            )

            if not permission:

                self.on_status(
                    "Microphone permission denied.",
                    "red"
                )

                return


            # ------------------------------------------------
            # Reset everything
            # ------------------------------------------------

            with self.lock:

                self.audio_buffer = bytearray()

                self.transcription_buffer = bytearray()

            self.final_text = ""

            self.speech_started = False

            self.transcribing = False

            self.stop_in_progress = False

            self.record_start_time = time.time()

            self.last_voice_time = time.time()

            self.last_transcription_time = time.time()


            # ------------------------------------------------
            # Recording state
            # ------------------------------------------------

            self.is_recording = True

            self.on_recording_change(True)

            self.on_status(
                "Listening...",
                "blue"
            )


            # ------------------------------------------------
            # Start recorder
            # ------------------------------------------------

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


            # ------------------------------------------------
            # Start silence watcher
            # ------------------------------------------------

            self.watch_task = asyncio.create_task(
                self._watch_recording()
            )

        except Exception as ex:

            self.is_recording = False

            self.on_recording_change(False)

            self.on_status(
                f"Microphone error: {ex}",
                "red"
            )


    # ============================================================
    # AUDIO STREAM
    # ============================================================

    def _on_audio_stream(
        self,
        e: far.AudioRecorderStreamEvent
    ):

        if not self.is_recording:

            return

        try:

            chunk = e.chunk

            if not chunk:

                return


            # ------------------------------------------------
            # Save audio safely
            # ------------------------------------------------

            with self.lock:

                if not self.is_recording:

                    return

                self.audio_buffer.extend(chunk)

                self.transcription_buffer.extend(chunk)


            # ------------------------------------------------
            # Detect voice
            # ------------------------------------------------

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


            if rms > RMS_THRESHOLD:

                self.speech_started = True

                self.last_voice_time = time.time()


            # ------------------------------------------------
            # Live transcription trigger
            # ------------------------------------------------

            now = time.time()

            if (
                self.speech_started
                and
                not self.transcribing
                and
                (
                    now - self.last_transcription_time
                    >= TRANSCRIBE_INTERVAL
                )
            ):

                self.last_transcription_time = now

                # Take current transcription audio
                with self.lock:

                    audio_for_transcription = bytes(
                        self.transcription_buffer
                    )

                    self.transcription_buffer = bytearray()


                if audio_for_transcription:

                    self.transcribing = True

                    self.page.run_thread(
                        self._transcribe_chunk,
                        audio_for_transcription
                    )

        except Exception as ex:

            print(
                "Audio stream error:",
                ex
            )


    # ============================================================
    # TRANSCRIBE CHUNK
    # ============================================================

    def _transcribe_chunk(
        self,
        audio_bytes
    ):

        try:

            if not audio_bytes:

                return


            # ------------------------------------------------
            # SpeechRecognition audio
            # ------------------------------------------------

            audio_data = sr.AudioData(
                audio_bytes,
                SAMPLE_RATE,
                BYTES_PER_SAMPLE
            )


            # ------------------------------------------------
            # Google speech recognition
            # ------------------------------------------------

            text = self.recognizer.recognize_google(
                audio_data,
                language="en-IN"
            )


            text = text.strip()

            if not text:

                return


            # ------------------------------------------------
            # Add text
            # ------------------------------------------------

            self._add_live_text(text)


        except sr.UnknownValueError:

            # Small chunks often don't contain a complete
            # recognizable sentence. Ignore this silently.

            pass


        except sr.RequestError as ex:

            print(
                "Speech service error:",
                ex
            )


            self.page.run_task(
                self._show_status,
                f"Speech service error: {ex}",
                "red"
            )


        except Exception as ex:

            print(
                "Transcription error:",
                ex
            )

        finally:

            self.transcribing = False


    # ============================================================
    # ADD LIVE TEXT
    # ============================================================

    def _add_live_text(self, new_text):

        new_text = new_text.strip()

        if not new_text:

            return


        # ------------------------------------------------
        # Avoid obvious duplicate text
        # ------------------------------------------------

        if self.final_text:

            old_words = self.final_text.lower().split()

            new_words = new_text.lower().split()


            # Find overlap between end of old text
            # and beginning of new text.

            overlap = 0

            max_overlap = min(
                6,
                len(old_words),
                len(new_words)
            )


            for n in range(
                max_overlap,
                0,
                -1
            ):

                if (
                    old_words[-n:]
                    ==
                    new_words[:n]
                ):

                    overlap = n

                    break


            if overlap:

                new_text = " ".join(
                    new_text.split()[overlap:]
                )


        if not new_text:

            return


        # ------------------------------------------------
        # Append
        # ------------------------------------------------

        if self.final_text:

            self.final_text += " "

        self.final_text += new_text


        # ------------------------------------------------
        # Send to TextField
        # ------------------------------------------------

        self.page.run_task(
            self._deliver_text,
            self.final_text
        )


    # ============================================================
    # DELIVER TEXT TO HOME SCREEN
    # ============================================================

    async def _deliver_text(self, text):

        try:

            self.on_result(text)

        except Exception as ex:

            print(
                "Result callback error:",
                ex
            )


    # ============================================================
    # STATUS
    # ============================================================

    async def _show_status(
        self,
        text,
        color="white"
    ):

        try:

            self.on_status(
                text,
                color
            )

        except Exception as ex:

            print(
                "Status callback error:",
                ex
            )


    # ============================================================
    # WATCH RECORDING
    # ============================================================

    async def _watch_recording(self):

        while self.is_recording:

            await asyncio.sleep(0.1)

            if not self.is_recording:

                return


            now = time.time()


            # ------------------------------------------------
            # Auto stop after silence
            # ------------------------------------------------

            if (
                self.speech_started
                and
                (
                    now - self.last_voice_time
                    >= SILENCE_SECONDS
                )
            ):

                await self.stop_recording()

                return


            # ------------------------------------------------
            # Maximum recording time
            # ------------------------------------------------

            if (
                now - self.record_start_time
                >= MAX_RECORD_SECONDS
            ):

                await self.stop_recording()

                return


    # ============================================================
    # STOP RECORDING
    # ============================================================

    async def stop_recording(self):

        if not self.is_recording:

            return

        if self.stop_in_progress:

            return


        self.stop_in_progress = True

        self.is_recording = False


        # ------------------------------------------------
        # UI
        # ------------------------------------------------

        self.on_recording_change(False)


        try:

            # ------------------------------------------------
            # Stop recorder safely
            # ------------------------------------------------

            try:

                await self.recorder.stop_recording()

            except Exception as ex:

                print(
                    "Recorder stop error:",
                    ex
                )


            # ------------------------------------------------
            # Get remaining transcription audio
            # ------------------------------------------------

            with self.lock:

                remaining_audio = bytes(
                    self.transcription_buffer
                )

                self.transcription_buffer = bytearray()


            # ------------------------------------------------
            # Transcribe remaining audio
            # ------------------------------------------------

            if remaining_audio:

                self.transcribing = True

                self._transcribe_chunk(
                    remaining_audio
                )

                self.transcribing = False


            # ------------------------------------------------
            # Final result
            # ------------------------------------------------

            if self.final_text:

                self.on_status(
                    "",
                    "white"
                )

            else:

                self.on_status(
                    "Kuch bola nahi gaya.",
                    "red"
                )


        except Exception as ex:

            print(
                "Stop recording error:",
                ex
            )

            self.on_status(
                f"Error: {ex}",
                "red"
            )

        finally:

            self.stop_in_progress = False

            self.speech_started = False
