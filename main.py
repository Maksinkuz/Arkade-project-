import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from views import MainMenu

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = MainMenu()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()