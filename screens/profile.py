import flet as ft
import asyncio
from database.db import ChatBotDatabase


def get_initials(name):
    parts = (name or "").strip().split()
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[1][0].upper()
    return parts[0][0].upper() if parts else "You"


def ProfileScreen(page: ft.Page, user_id, user_name=None):
    page.clean()
    from screens.home import HomeScreen

    page.theme_mode = ft.ThemeMode.DARK
    async def go_home(e):
        await HomeScreen(page, user_id, user.get("name", user_name))

    db = ChatBotDatabase()
    user = db.get_users_by_id(user_id) or {}

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Home",
            on_click=go_home
        ),
        title=ft.Text("Profile", color="white", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    avatar = ft.CircleAvatar(
        content=ft.Text(get_initials(user.get("name", user_name)), weight=ft.FontWeight.BOLD, size=28),
        radius=44,
        bgcolor=ft.Colors.BLUE,
    )

    name_field = ft.TextField(
        label="Name",
        value=user.get("name", ""),
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
        width=320,
    )
    email_field = ft.TextField(
        label="Email",
        value=user.get("email", ""),
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
        width=320,
    )
    mobile_field = ft.TextField(
        label="Mobile",
        value=user.get("mobile", ""),
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
        width=320,
    )
    password_field = ft.TextField(
        label="Password",
        value=user.get("password", ""),
        password=True,
        can_reveal_password=True,
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
        width=320,
    )

    status_text = ft.Text("", size=12)
    save_progress = ft.ProgressBar(width=320, visible=False)

    is_editing = False

    def set_editing(editing: bool):
        nonlocal is_editing
        is_editing = editing
        name_field.disabled = not editing
        email_field.disabled = not editing
        mobile_field.disabled = not editing
        password_field.disabled = not editing
        # NOTE: ElevatedButton's label lives in `.content`, not `.text` —
        # this Flet version has no `.text` property, so setting `.text`
        # was a silent no-op that never changed the visible label (only
        # `.icon` actually updated, which is why the icon flipped to Save
        # but the label stayed stuck on "Edit").
        edit_save_button.content = "Save" if editing else "Edit"
        edit_save_button.icon = ft.Icons.SAVE if editing else ft.Icons.EDIT
        page.update()

    async def edit_save_click(e):
        if not is_editing:
            status_text.value = ""
            set_editing(True)
            return

        # ---- Save ----
        name = name_field.value.strip()
        email = email_field.value.strip()
        mobile = mobile_field.value.strip()
        password_to_save = password_field.value.strip()

        if not name or not email or not mobile or not password_to_save:
            status_text.value = "No field can be left empty."
            status_text.color = "red"
            page.update()
            return  # stay in edit mode so they can fix it

        # Show the progress bar and lock the button while saving — the DB
        # call goes over the network (TiDB Cloud), so it isn't instant.
        edit_save_button.disabled = True
        save_progress.visible = True
        status_text.value = "Saving..."
        status_text.color = "blue"
        page.update()

        try:
            await asyncio.to_thread(
                db.update_profile, user_id, name, email, mobile, password_to_save
            )
        except Exception as ex:
            status_text.value = f"Failed to save: {ex}"
            status_text.color = "red"
            edit_save_button.disabled = False
            save_progress.visible = False
            page.update()
            return  # stay in edit mode so they can retry
        finally:
            save_progress.visible = False
            edit_save_button.disabled = False

        user["name"] = name
        user["email"] = email
        user["mobile"] = mobile
        user["password"] = password_to_save
        avatar.content.value = get_initials(name)
        status_text.value = "Profile updated!"
        status_text.color = "green"

        set_editing(False)  # locks fields again and flips button back to "Edit"

    edit_save_button = ft.ElevatedButton(
        "Edit",
        icon=ft.Icons.EDIT,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        on_click=edit_save_click,
        width=320,
    )

    content = ft.Column(
        controls=[
            ft.Container(height=10),
            avatar,
            ft.Container(height=20),
            name_field,
            email_field,
            mobile_field,
            password_field,
            ft.Container(height=10),
            edit_save_button,
            save_progress,
            status_text,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(
        ft.Container(content=content, padding=20, expand=True, alignment=ft.Alignment(0, 0)),
    )
    page.update()
