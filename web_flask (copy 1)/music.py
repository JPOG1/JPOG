import flet as ft

def main(page: ft.Page):
    page.title="increment counter"
    page.vertical_alignment=ft.MainAxisAlignment.CENTER
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER
    page.theme_mode= "yellow"
    page.bgcolor= ft.RadialGradient(colors=["yellow", "lightgrey"])
    def submit(e):
        print(username.value)
        print(password.value)
        
        
    username=ft.TextField(hint_text="username",prefix_icon=ft.icons.PERSON,bgcolor="grey",border=None,border_radius=30,password=False,width=500,)
    password=ft.TextField(prefix_icon=ft.icons.PASSWORD,hint_text="password",password= True,bgcolor= "grey",width=500,border=None,border_radius=30,suffix_icon=ft.icons.REMOVE_RED_EYE)
    page.add(
        ft.Column(
            alignment= ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                username,
                password,
                ft.FilledTonalButton(
                    "Login",
                    width= 500,
                    bgcolor="grey",  
                    on_click=submit                  
                )
            ]
        )
    )
    page.update()
    
if __name__ == '__main__':
    ft.app(target=main)