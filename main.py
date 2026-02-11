import arcade
import sqlite3
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from views import MainMenu

DB_NAME = "gamedata.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS levels (
            id INTEGER PRIMARY KEY,
            coins INTEGER,
            score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = MainMenu()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    init_db()
    main()