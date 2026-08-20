import flet as ft
import os
import asyncio
import google.generativeai as gn
gn.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = gn.GenerativeModel("gemini-3.6-flash")
def main(page:ft.Page):
    page.horizontal_alignment=ft.MainAxisAlignment.CENTER
    page.vertical_alignment=ft.CrossAxisAlignment.CENTER
 
    async def open_drawer(e):
     await page.show_drawer()
     
        
        
        
    
    chat_area = ft.Column(
        expand=True,

        scroll=ft.ScrollMode.AUTO,
        width=700
    )
    async def chats_clear(e):
     await page.close_drawer()
     chat_area.controls.clear()
     page.update()
      
    page.appbar = ft.AppBar(
    leading=ft.IconButton(
    icon=ft.Icons.MENU,
    icon_color=ft.Colors.WHITE,
    tooltip="menu",
    on_click=open_drawer
    ),
    bgcolor=ft.Colors.BLACK,
    
    )
    page.drawer = ft.NavigationDrawer(
    controls=[
        ft.ListTile(
             title=ft.Icon(
                ft.Icons.ASSISTANT,
                 color="white",size=60
             ),
            min_leading_width=200,
            leading=ft.Text(
                spans=[
                    ft.TextSpan(
                        "Chat",
                        style=ft.TextStyle(
                            color="red",
                            weight=ft.FontWeight.BOLD,
                            size=24
                        )
                    ),
                    ft.TextSpan(
                        "Bot",
                        style=ft.TextStyle(
                            color="blue",
                            weight=ft.FontWeight.BOLD,
                            size=24
                        )
                    )
                ]
            ),
        ),

        ft.Divider(),

        ft.ListTile(
            title=ft.Text(
                "Clear chat",
                color="red",
                weight=ft.FontWeight.BOLD
                
            ),
        
            leading=ft.Icon(
                ft.Icons.DELETE,
                color="red"
            ),
            on_click=chats_clear
        ),

        ft.Divider(),

        ft.ListTile(
            title=ft.Text(
                "New Chat",
                color="white",
                weight=ft.FontWeight.BOLD
            ),
        
            leading=ft.Icon(
                ft.Icons.CHAT,
                color="white"
            )
        )
    ]
    )
    
    def show_msg(sender,message):
        
    
     
     
        chat_area.controls.append(
            ft.Container(
               
                ft.Text(
                    spans=[
                        ft.TextSpan(
                            f"{sender}",
                            style=ft.TextStyle(color="red",weight=ft.FontWeight.BOLD),
                        ),
                        ft.TextSpan(
                           f"{message}",
                           style=ft.TextStyle(color="white",weight=ft.FontWeight.BOLD)
                        )
                    ],
                    selectable=True
                ),
                padding=0,
                margin=5,
                border_radius=5
            )
            chat_area.controls.append(
        ft.Divider(
            height=1,
            color=ft.Colors.WHITE_24
        ))
        page.update()
    async def send_msg(e):
        user = user_msg.value.strip()
        if not user:
            return
        show_msg("",user)    
        
        user_msg.value = ""
    
        user_msg.hint_text = "Thinking..."
        user_msg.disabled = True
        user_msg.hint_style=ft.TextStyle(color="blue")
        page.update()
        try:
            response = await asyncio.to_thread(model.generate_content,user)
            show_msg("",response.text)
        except Exception as e:
            show_msg("Error",str(e)) 
        finally:
            user_msg.hint_text = "Ask anything..."
            user_msg.hint_style = ft.TextStyle(color="white")
            user_msg.disabled=False
            page.update()     

    user_msg = ft.TextField(
        hint_text="Ask anything...",
        hint_style=ft.TextStyle(color="white"),
        value="",
        autofocus=True,
        expand=True,
        align=ft.Alignment.BOTTOM_CENTER,
        on_submit=send_msg,
        
        suffix=ft.IconButton(
            icon=ft.Icons.SEND_OUTLINED,
            icon_color="blue",
            # bgcolor="blue",
            on_click=send_msg,
            tooltip="Send..."
            
        ),
        
        height=60,
        margin=5,
        border_color=ft.Colors.WHITE_24,
        width=500,
        border_radius=20,
        color="white"
   
    )
    page.add(
       
        chat_area,
        ft.Row(
            controls=[
                user_msg,
                

            ]
            
        )
    )
ft.run(main)

