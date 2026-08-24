import flet as ft
import os
import io
import mimetypes
import base64
import asyncio
import google.generativeai as gn
from dotenv import load_dotenv
from PIL import Image


load_dotenv()  # reads .env in your project root

gn.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = gn.GenerativeModel("gemini-3.6-flash")

# 1x1 transparent PNG placeholder — see camera.py for why this is needed.
_BLANK_PIXEL = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42Y"
    "AAAAASUVORK5CYII="
)


async def HomeScreen(page: ft.Page, user_id, name):
    page.clean()
    from database.db import ChatBotDatabase
    from screens.chat_history import ChatHistory 
    from screens.login import LoginScreen
    from screens.camera import CameraScreen
    from screens.mic import MicScreen
    from screens.photo import GalleryScreen
    from screens.file import FileScreen
    from screens.setting import SettingScreen
    from screens.profile import ProfileScreen

    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 360
    page.window.height = 700

    db = ChatBotDatabase()

    def get_initials(name):
        parts = name.strip().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        return parts[0][0].upper() if parts else "You"    

    def Navigation(action):
        async def handler(e):
            await page.close_drawer()
            action(e)
        return handler

    async def open_drawer(e):
        await page.show_drawer()

    async def chats_clear(e):
        await page.close_drawer()
        chat_area.controls.clear()
        page.update()

    async def LogOut(e):
        await page.close_drawer()
        page.appbar = None
        page.drawer = None

        snack = ft.SnackBar(
            content=ft.Text("Logouting....", color="red"),
            shape=ft.RoundedRectangleBorder(radius=12),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=20,
            width=300,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

        LoginScreen(page)

    # ---- upload popup widgets (declared before CameraScreen so callbacks can use them) ----
    uploaded_image_preview = ft.Image(
        src=_BLANK_PIXEL,
        width=150,
        height=120,
        fit=ft.BoxFit.CONTAIN,
        visible=False,
    )
    upload_progress = ft.ProgressBar(value=0)
    upload_status = ft.Text("")

    # Image/file the user has attached but not yet sent — nothing is sent
    # to Gemini until they actually press Send. Only one attachment (image
    # OR file) is kept at a time.
    pending_image_path = None
    pending_image_b64 = None
    pending_file_path = None
    pending_file_name = None
    pending_file_bytes = None

    def set_status(text, color="white"):
        upload_status.value = text
        upload_status.color = color
        page.update()

    attachment_thumb = ft.Image(
        src=_BLANK_PIXEL,
        width=44,
        height=44,
        fit=ft.BoxFit.COVER,
        border_radius=8,
        visible=False,
    )
    attachment_file_icon = ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="blue", size=36, visible=False)
    attachment_label = ft.Text("", color="white", size=12, expand=True)

    def clear_attachment(e=None):
        """Fully resets BOTH image and file attachment state/visuals. This
        is the single place that clears things, so switching from an image
        to a file (or vice versa) always starts from a clean slate."""
        nonlocal pending_image_path, pending_image_b64
        nonlocal pending_file_path, pending_file_name, pending_file_bytes

        pending_image_path = None
        pending_image_b64 = None
        pending_file_path = None
        pending_file_name = None
        pending_file_bytes = None

        uploaded_image_preview.src = _BLANK_PIXEL
        uploaded_image_preview.visible = False

        attachment_thumb.src = _BLANK_PIXEL
        attachment_thumb.visible = False

        attachment_file_icon.visible = False
        attachment_label.value = ""
        set_attachment_visible(False)
        page.update()

    attachment_bar = ft.Row(
        controls=[
            attachment_thumb,
            attachment_file_icon,
            attachment_label,
            ft.IconButton(icon=ft.Icons.CLOSE, icon_color="white", icon_size=16, tooltip="Remove", on_click=clear_attachment),
        ],
        spacing=5,
    )

    attachment_container = ft.Container(
        content=attachment_bar,
        height=0,
        opacity=0,
        animate_opacity=250,
        animate_size=250,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    def set_attachment_visible(show: bool):
        attachment_container.height = 50 if show else 0
        attachment_container.opacity = 1 if show else 0
        page.update()

    def on_photo_captured(img_path, b64_jpeg):
        """Called by CameraScreen/GalleryScreen once a photo is ready. Just
        attaches the photo — nothing is sent to Gemini until the user
        presses Send. Replaces any previously attached image or file."""
        nonlocal pending_image_path, pending_image_b64
        clear_attachment()  # wipes any previous image AND any previous file
        pending_image_path = img_path
        pending_image_b64 = b64_jpeg

        uploaded_image_preview.src = b64_jpeg
        uploaded_image_preview.visible = True
        set_status(f"Photo captured: {img_path}", "green")

        attachment_thumb.src = b64_jpeg
        attachment_thumb.visible = True
        attachment_file_icon.visible = False
        attachment_label.value = "Image attached — write a caption or just send."
        set_attachment_visible(True)

        if dialog.open:
            page.pop_dialog()
        page.update()

    camera_screen = CameraScreen(page, on_status=set_status, on_captured=on_photo_captured)

    gallery_screen = GalleryScreen(page, on_status=set_status, on_picked=on_photo_captured)

    def on_file_picked(path, filename, file_bytes):
        nonlocal pending_file_path, pending_file_name, pending_file_bytes
        clear_attachment()

        pending_file_path = path
        pending_file_name = filename
        pending_file_bytes = file_bytes

        attachment_file_icon.visible = True
        attachment_thumb.visible = False
        attachment_label.value = f"{filename} attached — write a note or just send."
        set_attachment_visible(True)
        set_status(f"File selected: {filename}", "green")

        if dialog.open:
            page.pop_dialog()
        page.update()

    file_screen = FileScreen(page, on_status=set_status, on_picked=on_file_picked)

    # ---- mic: click to start recording, click again to stop + transcribe ----
    def on_mic_status(text, color="white"):
        user_msg.hint_text = text if text else "Ask anything...."
        page.update()

    def on_mic_recording_change(is_recording):
        mic_button.icon = ft.Icons.STOP_CIRCLE if is_recording else ft.Icons.MIC
        mic_button.icon_color = "red" if is_recording else "blue"
        page.update()

    def on_mic_result(text):
        user_msg.value = text
        page.update()

    mic_screen = MicScreen(
        page,
        on_status=on_mic_status,
        on_result=on_mic_result,
        on_recording_change=on_mic_recording_change,
    )

    mic_button = ft.IconButton(
        icon=ft.Icons.MIC,
        icon_color="blue",
        tooltip="Voice",
        on_click=mic_screen.toggle_mic,
    )

    camera_tile = ft.ListTile(
        title=ft.Text("Camera", color="white", weight=ft.FontWeight.BOLD),
        leading=ft.Icon(ft.Icons.CAMERA_ALT, color="blue"),
    )

    async def handle_camera_click(e):
        # open_camera itself reports status now (it needs to open the
        # dialog before it can even check for a camera), so it handles
        # "Opening camera..." / errors on its own.
        await camera_screen.open_camera(e)

    camera_tile.on_click = handle_camera_click

    column = ft.Column(
        controls=[
            camera_tile,
            ft.Divider(),
            ft.ListTile(
                title=ft.Text("Image", color="white", weight=ft.FontWeight.BOLD),
                leading=ft.Icon(ft.Icons.IMAGE, color="blue"),
                on_click=gallery_screen.open_gallery,
            ),
            ft.Divider(),
            ft.ListTile(
                title=ft.Text("Files", color="white", weight=ft.FontWeight.BOLD),
                leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="blue"),
                on_click=file_screen.open_file_picker,
            ),
            ft.Divider(),
            ft.ListTile(leading=upload_progress),
            ft.Container(
                content=uploaded_image_preview,
                alignment=ft.Alignment(0, 0),
                margin=10,
            ),
        ],
    )

    def close_dialog(e):
        try:
            if dialog.open:
                page.pop_dialog()
            else:
                page.update()
        except Exception as ex:
            print(f"close_dialog: {ex}")

    dialog = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Text(
                    spans=[
                        ft.TextSpan("Up", style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD, size=15)),
                        ft.TextSpan("load", style=ft.TextStyle(color="blue", weight=ft.FontWeight.BOLD, size=15)),
                    ]
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color="white",
                    icon_size=18,
                    tooltip="Close",
                    on_click=close_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        content=ft.Column(
            [column, upload_status],
            tight=True,
            height=400,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    def open_upload_popup(e):
        upload_status.value = ""
        if not user_msg.disabled:
            upload_progress.value = 0
        try:
            page.show_dialog(dialog)
        except Exception as ex:
            # Guards against rapid double-taps trying to open the dialog
            # twice, or the dialog stack being briefly out of sync.
            print(f"open_upload_popup: {ex}")
            page.update()

    chat_area = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        width=700,
    )

    def show_msg(sender, message):
        # Wrapped in try/except: if the websocket connection has already
        # dropped (browser tab closed/refreshed, or a huge payload caused
        # a disconnect), this keeps that failure from crashing the rest of
        # the app's event handling — it just silently fails to render that
        # one message instead of raising all the way up.
        try:
            # NOTE: check startswith("[Image]|||") specifically, not just
            # "|||" in message. A loose substring check would misfire on
            # any ordinary AI reply that happens to contain "|||" (a
            # table, code, etc.) and try to parse it as an image — and if
            # the exact "[Image]|||" prefix isn't actually present,
            # b64_data ends up as an empty string, which crashes ft.Image
            # ("A valid src value must be specified.").
            if message.startswith("[Image]|||"):
                try:
                    _, _, data_part = message.partition("[Image]|||")
                    b64_data, _, caption_text = data_part.partition("|||")

                    if not caption_text:
                        caption_text = "Photo Attachment"

                    if not b64_data:
                        img_src = _BLANK_PIXEL  # never pass an empty src
                    elif not b64_data.startswith("data:image"):
                        img_src = f"data:image/jpeg;base64,{b64_data}"
                    else:
                        img_src = b64_data

                    chat_area.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Image(
                                    src=img_src,
                                    width=220,
                                    height=165,
                                    fit=ft.BoxFit.CONTAIN,
                                    border_radius=8,
                                ),
                                ft.Text(caption_text, color="white", weight=ft.FontWeight.BOLD)
                            ]),
                            margin=5,
                            padding=10,
                            bgcolor=ft.Colors.WHITE_10,
                            border_radius=8
                        )
                    )
                except Exception:
                    chat_area.controls.append(ft.Text("[Image Attachment]", color="white"))

            elif message.startswith("[File]"):
                clean_text = message.replace("[File]", "").strip()
                chat_area.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="blue", size=20),
                            ft.Text(clean_text, color="white", weight=ft.FontWeight.BOLD)
                        ], spacing=10),
                        margin=5,
                        padding=10,
                        bgcolor=ft.Colors.WHITE_10,
                        border_radius=8
                    )
                )

            else:
                display_sender = f"{sender} " if sender else ""
                chat_area.controls.append(
                    ft.Container(
                        ft.Text(
                            spans=[
                                ft.TextSpan(display_sender, style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD)),
                                ft.TextSpan(f"{message}", style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD)),
                            ],
                            selectable=True,
                        ),
                        padding=0,
                        margin=5,
                        border_radius=5,
                    )
                )

            page.update()
        except Exception as ex:
            print(f"show_msg: failed to render/send message ({ex}); continuing.")

    async def send_msg(e):
        nonlocal pending_image_path, pending_image_b64
        nonlocal pending_file_path, pending_file_name, pending_file_bytes

        text = user_msg.value.strip()
        image_path = pending_image_path
        image_b64 = pending_image_b64
        file_path = pending_file_path
        file_name = pending_file_name
        file_bytes = pending_file_bytes
        has_file = bool(file_path or file_bytes)

        if not text and not image_path and not has_file:
            return  

        if image_path:
            show_image_msg(image_b64)
        if has_file:
            show_file_msg(file_name)
        if text:
            show_msg("", text)

        user_msg.value = ""
        clear_attachment()

        user_msg.hint_text = "Thinking...."
        user_msg.hint_style = ft.TextStyle(color="blue")
        user_msg.disabled = True
        if image_path or has_file:
            upload_progress.value = None
        page.update()

        try:
            if image_path:
                prompt = text if text else "Describe this image."
                pil_image = Image.open(image_path)
                response = await asyncio.to_thread(
                    model.generate_content, [prompt, pil_image]
                )
                caption = text if text else "Photo Attachment"
                db_text = f"[Image]|||{image_b64}|||{caption}"

            elif has_file:
                prompt = text if text else "Summarize this file."
                if file_path:
                    uploaded_file = await asyncio.to_thread(gn.upload_file, file_path)
                else:
                    guessed_mime, _ = mimetypes.guess_type(file_name or "")
                    file_obj = io.BytesIO(file_bytes)
                    uploaded_file = await asyncio.to_thread(
                        gn.upload_file,
                        file_obj,
                        mime_type=guessed_mime or "application/octet-stream",
                        display_name=file_name,
                    )
                response = await asyncio.to_thread(
                    model.generate_content, [prompt, uploaded_file]
                )
                note = f" ({text})" if text else ""
                db_text = f"[File] {file_name}{note}"
            else:
                response = await asyncio.to_thread(model.generate_content, text)
                db_text = text

            show_msg("", response.text)

            db.save_ai_chat(user_id, db_text, response.text)

            await asyncio.sleep(0.1)
            history_sidebar.refresh()

        except Exception as err:
            show_msg("Error: ", str(err))
        finally:
            if image_path or has_file:
                upload_progress.value = 1  
            user_msg.hint_text = "Ask anything...."
            user_msg.hint_style = ft.TextStyle(color="white")
            user_msg.disabled = False
            page.update()

    history_sidebar = ChatHistory(page, user_id, chat_area, show_msg, db=db)

    def new_chat(e):
        chat_area.controls.clear()
        user_msg.value = ""
        clear_attachment()
        user_msg.hint_text = "Ask anything...."
        user_msg.disabled = False
        upload_progress.value = 0
        # Otherwise, deleting the chat that was open before "New Chat" was
        # pressed would wrongly clear this freshly-started conversation too.
        history_sidebar.current_chat_id = None
        history_sidebar.refresh()
        page.update()

    async def open_profile(e):
        await page.close_drawer()
        ProfileScreen(page, user_id, name)

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.WHITE,
            tooltip="Menu",
            margin=5,
            on_click=open_drawer,
        ),
        actions=[
            ft.OutlinedButton(
                "new", 
                ft.Icon(ft.Icons.EDIT, color="white"), 
                tooltip="new", margin=5,
                on_click=new_chat
                ),
            ft.IconButton(
                icon=ft.Icons.ADD,
                icon_color="white",
                tooltip="attach",
                bgcolor=ft.Colors.WHITE_10,
                margin=5,
                padding=0,
                on_click=open_upload_popup,
            ),
        ],
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Column(
                expand=True,
                controls=[
                    ft.ListTile(
                        trailing=ft.GestureDetector(
                        content=ft.CircleAvatar(
                            content=ft.Text(
                                get_initials(name),
                                weight=ft.FontWeight.BOLD,
                            ),
                            radius=25,
                        ),
                        on_tap=open_profile ,
                        tooltip="Go profile"
                        ),
                        min_leading_width=250,
                        leading=ft.Text(
                            spans=[
                                ft.TextSpan("Chat", style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD, size=24)),
                                ft.TextSpan("Bot", style=ft.TextStyle(color="blue", weight=ft.FontWeight.BOLD, size=24)),
                            ]
                        ),
                        margin=10
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        title=ft.Text("Home", color="white",weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.HOME, color="white"),
                        on_click=Navigation(lambda e:HomeScreen(page,user_id,name)),
                        tooltip="Home"
                    ),
                    ft.Divider(),

                    ft.ListTile(
                        title=ft.Text("Clear chat", color="red", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.DELETE, color="red"),
                        on_click=chats_clear,
                        tooltip="chat clear."
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        title=ft.Text(
                            "Chat History",
                            color="white",
                            weight=ft.FontWeight.BOLD,
                        ),
                        leading=ft.Icon(
                            ft.Icons.HISTORY,
                            color="blue",
                        ),
                    ),

                   ft.Container(
                     expand=True,
                       content=ft.Column(
                      controls=[history_sidebar.view],
                     scroll=ft.ScrollMode.AUTO,
                      expand=True,
                      ),
                    ),

                
                    ft.Divider(),
                    ft.ListTile(
                        title=ft.Text("Setting", color="white", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.SETTINGS, color="green"),
                        on_click=Navigation(lambda e: SettingScreen(page,user_id,name)),
                        tooltip="Setting"
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED),
                        title=ft.Text("Logout"),
                        on_click=LogOut,
                        tooltip="Logout."
                    ),
                ],
            )
        ]
    )
    # ---- tap-to-zoom viewer for sent images/files ----
    viewer_image = ft.Image(
        src=_BLANK_PIXEL,
        fit=ft.BoxFit.CONTAIN,
        border_radius=8,
    )
    viewer_file_icon = ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="blue", size=96, visible=False)
    viewer_filename = ft.Text("", color="white", weight=ft.FontWeight.BOLD, size=16, visible=False)

    viewer_content = ft.Container(
        content=ft.Column(
            controls=[viewer_image, viewer_file_icon, viewer_filename],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=320,
        height=320,
        alignment=ft.Alignment(0, 0),
        scale=0.3,
        opacity=0,
        animate_scale=250,
        animate_opacity=250,
    )

    async def close_viewer(e=None):
        viewer_content.scale = 0.3
        viewer_content.opacity = 0
        page.update()
        await asyncio.sleep(0.22)
        if viewer_dialog.open:
            page.pop_dialog()

    viewer_dialog = ft.AlertDialog(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_color="white", tooltip="Close", on_click=close_viewer),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                viewer_content,
            ],
            tight=True,
        ),
        on_dismiss=lambda e: None,
    )

    async def open_image_viewer(b64_jpeg):
        viewer_image.src = b64_jpeg
        viewer_image.visible = True
        viewer_file_icon.visible = False
        viewer_filename.visible = False
        viewer_content.scale = 0.3
        viewer_content.opacity = 0
        page.show_dialog(viewer_dialog)
        await asyncio.sleep(0.03)
        viewer_content.scale = 1
        viewer_content.opacity = 1
        page.update()

    async def open_file_viewer(filename):
        viewer_image.visible = False
        viewer_file_icon.visible = True
        viewer_filename.value = filename
        viewer_filename.visible = True
        viewer_content.scale = 0.3
        viewer_content.opacity = 0
        page.show_dialog(viewer_dialog)
        await asyncio.sleep(0.03)
        viewer_content.scale = 1
        viewer_content.opacity = 1
        page.update()

    def show_image_msg(b64_jpeg):
        chat_area.controls.append(
            ft.Container(
                content=ft.Image(
                    src=b64_jpeg,
                    width=220,
                    height=165,
                    fit=ft.BoxFit.CONTAIN,
                    border_radius=8,
                ),
                padding=0,
                margin=5,
                on_click=lambda e, b64=b64_jpeg: page.run_task(open_image_viewer, b64),
            )
        )
        page.update()

    def show_file_msg(filename):
        chat_area.controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="blue"),
                        ft.Text(filename, color="white", weight=ft.FontWeight.BOLD, selectable=True),
                    ],
                    spacing=8,
                ),
                padding=8,
                margin=5,
                border_radius=8,
                bgcolor=ft.Colors.WHITE_10,
                on_click=lambda e, name=filename: page.run_task(open_file_viewer, name),
            )
        )
        page.update()

    user_msg = ft.TextField(
        hint_text="Ask anything...",
        hint_style=ft.TextStyle(color="white"),
        value="",
        autofocus=True,
        expand=True,
        align=ft.Alignment.BOTTOM_CENTER,
        on_submit=send_msg,
        suffix=ft.Row(
            controls=[
                mic_button,
                ft.IconButton(icon=ft.Icons.SEND_OUTLINED, icon_color="blue", on_click=send_msg, tooltip="send.."),
            ],
            tight=True,
            spacing=0,
        ),
        height=60,
        margin=5,
        border_color=ft.Colors.WHITE_24,
        width=500,
        border_radius=20,
        color="white",
        tooltip="Ask here anything....."
    )

    page.add(
        chat_area,
        attachment_container,
        ft.Row([user_msg]),
    )
    page.update()
