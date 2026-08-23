import flet as ft
import cv2
import base64
import threading
import time
import os

# 1x1 transparent PNG, used as a placeholder so ft.Image always has a
# valid src (Flet raises "A valid src value must be specified."
# if src is empty when the control renders). In this Flet version, src
# itself accepts a URL, a base64 string, or raw bytes - there is no
# separate src_base64 property.
_BLANK_PIXEL = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42Y"
    "AAAAASUVORK5CYII="
)


class CameraScreen:
    """
    Live camera popup.

    Instead of scanning page.overlay and guessing control indexes (which was
    fragile and broke whenever the layout changed), the caller (home.py)
    passes in:
      - on_status(text, color): called to update a status message
      - on_captured(image_path, b64_jpeg): called once a photo is captured
    """

    def __init__(self, page: ft.Page, on_status=None, on_captured=None):
        self.page = page
        self.cap = None
        self.is_streaming = False
        self.on_status = on_status or (lambda text, color="white": None)
        self.on_captured = on_captured or (lambda path, b64: None)

        self.camera_preview = ft.Image(
            src=_BLANK_PIXEL,
            width=280,
            height=210,
            fit=ft.BoxFit.CONTAIN,
        )

        self.camera_dialog = ft.AlertDialog(
            title=ft.Text("Live Camera", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    self.camera_preview,
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Capture",
                            icon=ft.Icons.CAMERA_ALT,
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            on_click=self.capture_photo,
                        ),
                        alignment=ft.Alignment(0, 0),
                        margin=10,
                    ),
                ],
                tight=True,
                width=300,
            ),
            on_dismiss=self.on_dialog_close,
        )

    def open_camera(self, e):
        self.on_status("Opening camera...", "blue")

        self.page.show_dialog(self.camera_dialog)
        self.is_streaming = True

        # Run the blocking OpenCV loop in a background thread so it never
        # blocks Flet's websocket / event loop.
        threading.Thread(target=self._stream_camera, daemon=True).start()

    def _stream_camera(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            self.on_status("Camera hardware not found!", "red")
            self.close_camera_popup()
            return

        # Keep the capture device itself at a small resolution so we're not
        # reading (and then downscaling) huge frames every loop.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        consecutive_failures = 0
        jpeg_params = [int(cv2.IMWRITE_JPEG_QUALITY), 55]

        while self.is_streaming and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            _, buffer = cv2.imencode(".jpg", frame, jpeg_params)
            b64_string = base64.b64encode(buffer).decode("utf-8")
            self.camera_preview.src = b64_string

            try:
                # Update just this control, not the whole page — much
                # smaller payload over the websocket than page.update().
                self.camera_preview.update()
                consecutive_failures = 0
            except Exception:
                # The websocket hiccuped/disconnected for this frame.
                # Don't crash the thread — just skip the frame and retry.
                consecutive_failures += 1
                if consecutive_failures > 20:
                    # Connection is genuinely gone; stop trying.
                    self.is_streaming = False
                    break

            # ~12 fps is plenty for a preview and is far gentler on the
            # websocket than the original ~33 fps.
            time.sleep(0.08)

        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_photo(self, e):
        try:
            if not (self.cap and self.cap.isOpened()):
                raise Exception("Camera is not open.")

            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Failed to read frame from camera.")

            os.makedirs("assets", exist_ok=True)
            img_path = os.path.join("assets", f"captured_{int(time.time())}.jpg")
            cv2.imwrite(img_path, frame)

            _, buffer = cv2.imencode(".jpg", frame)
            captured_b64 = base64.b64encode(buffer).decode("utf-8")

            # Close the small live-camera popup first...
            self.close_camera_popup()

            # ...then hand the captured photo back to home.py to display
            # it and "upload" (send to Gemini) it.
            self.on_captured(img_path, captured_b64)

        except Exception as ex:
            self.on_status(f"Capture error: {ex}", "red")
            self.page.update()

    def close_camera_popup(self):
        self.is_streaming = False
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        if self.camera_dialog.open:
            self.page.pop_dialog()
        else:
            self.page.update()

    def on_dialog_close(self, e):
        # Fires if the user dismisses the popup by tapping outside it.
        self.is_streaming = False
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()