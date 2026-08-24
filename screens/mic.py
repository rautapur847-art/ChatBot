import flet as ft
import numpy as np
import speech_recognition as sr
import threading
import time


# =========================================================
# SOUNDDEVICE IMPORT
# =========================================================

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True

except (OSError, ImportError):
    sd = None
    SOUNDDEVICE_AVAILABLE = False


# =========================================================
# SETTINGS
# =========================================================

SAMPLE_RATE = 16000
CHANNELS = 1

RMS_THRESHOLD = 300
SILENCE_SECONDS = 1.2
MAX_RECORD_SECONDS = 15


# =========================================================
# MIC SCREEN
# =========================================================

class MicScreen:

    def __init__(
        self,
        page: ft.Page,
        on_status=None,
        on_result=None,
        on_recording_change=None
    ):

        self.page = page

        self.recognizer = sr.Recognizer()

        self.is_recording = False

        self.frames = []

        self.stream = None

        self.speech_started = False

        self.last_voice_time = 0.0

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
    # TOGGLE MIC
    # =====================================================

    def toggle_mic(self, e):

        if not SOUNDDEVICE_AVAILABLE:

            self.on_status(
                "Voice input isn't available on this deployment.",
                "red"
            )

            return


        if not self.is_recording:

            self.start_recording()

        else:

            self.stop_recording()


    # =====================================================
    # START RECORDING
    # =====================================================

    def start_recording(self):

        # Prevent duplicate start
        if self.is_recording:
            return


        # Reset recording state
        self.frames = []

        self.speech_started = False

        self.last_voice_time = time.time()

        self.is_recording = True


        self.on_recording_change(True)

        self.on_status(
            "Listening... boliye, khamoshi hote hi auto-stop hoga.",
            "blue"
        )


        # =================================================
        # AUDIO CALLBACK
        # =================================================

        def callback(
            indata,
            frame_count,
            time_info,
            status
        ):

            if not self.is_recording:
                return


            try:

                # Copy audio data
                self.frames.append(
                    indata.copy()
                )


                # Calculate RMS
                rms = float(
                    np.sqrt(
                        np.mean(
                            indata.astype(
                                np.float64
                            ) ** 2
                        )
                    )
                )


                # Detect speech
                if rms > RMS_THRESHOLD:

                    self.speech_started = True

                    self.last_voice_time = time.time()


            except Exception as ex:

                print(
                    f"Audio callback error: {ex}"
                )


        # =================================================
        # CREATE AUDIO STREAM
        # =================================================

        try:

            self.stream = sd.InputStream(

                samplerate=SAMPLE_RATE,

                channels=CHANNELS,

                dtype="int16",

                callback=callback,
            )


            self.stream.start()


            # Start silence watcher
            threading.Thread(
                target=self._watch_for_silence,
                daemon=True
            ).start()


        except Exception as ex:

            self.is_recording = False

            self.on_recording_change(False)

            self.stream = None

            self.on_status(
                f"Microphone error: {ex}",
                "red"
            )


    # =====================================================
    # WATCH SILENCE / AUTO STOP
    # =====================================================

    def _watch_for_silence(self):

        start_time = time.time()


        while self.is_recording:

            time.sleep(0.1)


            if not self.is_recording:
                return


            now = time.time()


            # ---------------------------------------------
            # AUTO STOP AFTER SILENCE
            # ---------------------------------------------

            if (
                self.speech_started
                and
                (now - self.last_voice_time)
                > SILENCE_SECONDS
            ):

                self.stop_recording()

                return


            # ---------------------------------------------
            # MAX RECORDING TIME
            # ---------------------------------------------

            if (
                now - start_time
            ) > MAX_RECORD_SECONDS:

                self.stop_recording()

                return


    # =====================================================
    # STOP RECORDING
    # =====================================================

    def stop_recording(self):

        # Already stopped
        if not self.is_recording:
            return


        # ---------------------------------------------
        # Stop recording state
        # ---------------------------------------------

        self.is_recording = False

        self.on_recording_change(False)


        # ---------------------------------------------
        # IMPORTANT:
        # Take snapshot of current recording
        # ---------------------------------------------

        frames = self.frames.copy()

        speech_started = self.speech_started


        # Reset current recording
        # New recording will get fresh frames

        self.frames = []

        self.speech_started = False


        # ---------------------------------------------
        # Stop audio stream safely
        # ---------------------------------------------

        if self.stream:

            try:

                self.stream.stop()

            except Exception as ex:

                print(
                    f"Stream stop error: {ex}"
                )


            try:

                self.stream.close()

            except Exception as ex:

                print(
                    f"Stream close error: {ex}"
                )


            self.stream = None


        # ---------------------------------------------
        # Start transcription
        # ---------------------------------------------

        self.on_status(
            "Transcribing...",
            "blue"
        )


        threading.Thread(

            target=self._transcribe,

            args=(
                frames,
                speech_started
            ),

            daemon=True

        ).start()


    # =====================================================
    # TRANSCRIBE
    # =====================================================

    def _transcribe(
        self,
        frames,
        speech_started
    ):

        # ---------------------------------------------
        # Nothing recorded
        # ---------------------------------------------

        if (
            not frames
            or
            not speech_started
        ):

            self.on_status(
                "Kuch bola nahi gaya — dobara try karein.",
                "red"
            )

            return


        try:

            # -----------------------------------------
            # Combine audio frames
            # -----------------------------------------

            audio_np = np.concatenate(
                frames,
                axis=0
            )


            # -----------------------------------------
            # Convert to bytes
            # -----------------------------------------

            audio_bytes = audio_np.tobytes()


            # -----------------------------------------
            # SpeechRecognition AudioData
            # -----------------------------------------

            audio_data = sr.AudioData(

                audio_bytes,

                SAMPLE_RATE,

                2
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

            self.on_result(text)


        # =============================================
        # SPEECH NOT UNDERSTOOD
        # =============================================

        except sr.UnknownValueError:

            self.on_status(
                "Samajh nahi aaya — dobara try karein.",
                "red"
            )


        # =============================================
        # GOOGLE API ERROR
        # =============================================

        except sr.RequestError as ex:

            self.on_status(
                f"Speech service error: {ex}",
                "red"
            )


        # =============================================
        # OTHER ERROR
        # =============================================

        except Exception as ex:

            self.on_status(
                f"Error: {ex}",
                "red"
            )
