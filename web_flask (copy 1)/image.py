import flet as ft
import src


def main(page: ft.Page):
    page.title= "pictures"
    page.bgcolor="#171717"
    
    for file in src:
        files=ft.Image(f"{file}", fit=ft.ImageFit.FILL)
    page.add(
        ft.Row(
            files
        )
    )
    
    
if __name__=="__main__":
    ft.app(target=main)