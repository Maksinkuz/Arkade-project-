import arcade
import math

# --- Константы ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_TITLE = "Maze Shooter: Prototype"

# Параметры игрока
PLAYER_MOVEMENT_SPEED = 5
PLAYER_SCALE = 0.5

# Параметры пули
BULLET_SPEED = 20
BULLET_SCALE = 0.5
BULLET_DAMAGE = 10  # покка не используетс

# Спрайты (используем встроенные ресурсы Arcade)
RESOURCE_PLAYER = ":resources:images/animated_characters/female_person/femalePerson_idle.png"
RESOURCE_PLAYER_WALK = ":resources:images/animated_characters/female_person/femalePerson_walk0.png"
RESOURCE_ENEMY = ":resources:images/animated_characters/zombie/zombie_idle.png"
RESOURCE_WALL = ":resources:images/tiles/boxCrate_double.png"
RESOURCE_BULLET = ":resources:images/space_shooter/laserBlue01.png"


class MainMenu(arcade.View):
    """ Экран главного меню """

    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_BLUE_GRAY

    def on_draw(self):
        self.clear()
        arcade.draw_text("MAZE SHOOTER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("Нажмите ENTER для начала игры", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
                         arcade.color.GRAY, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)


class GameOverView(arcade.View):
    """ Экран окончания игры (результаты) """

    def __init__(self, score):
        super().__init__()
        self.score = score

    def on_show_view(self):
        self.window.background_color = arcade.color.BLACK

    def on_draw(self):
        self.clear()
        arcade.draw_text("ИГРА ОКОНЧЕНА", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.RED, font_size=50, anchor_x="center")
        arcade.draw_text(f"Ваш счет: {self.score}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, font_size=30, anchor_x="center")
        arcade.draw_text("Нажмите ENTER для перезапуска", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                         arcade.color.GRAY, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            menu_view = MainMenu()
            self.window.show_view(menu_view)


class Player(arcade.Sprite):
    """ Класс игрока с простой анимацией """

    def __init__(self):
        super().__init__(scale=PLAYER_SCALE)
        # Загружаем текстуры для анимации
        self.idle_texture = arcade.load_texture(RESOURCE_PLAYER)
        self.walk_texture = arcade.load_texture(RESOURCE_PLAYER_WALK)
        self.texture = self.idle_texture

    def update_animation(self, delta_time):
        # Если игрок двигается, меняем текстуру
        if abs(self.change_x) > 0 or abs(self.change_y) > 0:
            self.texture = self.walk_texture
        else:
            self.texture = self.idle_texture

        # Поворот спрайта в зависимости от направления
        if self.change_x < 0:
            self.texture = self.walk_texture.flip_left_right()
        elif self.change_x > 0:
            self.texture = self.walk_texture


class GameView(arcade.View):
    """ Основной класс игры """

    def __init__(self):
        super().__init__()
        # Scene управляет списками спрайтов
        self.scene = None
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None
        self.score = 0

        # Звуки
        self.shoot_sound = arcade.load_sound(":resources:sounds/laser1.wav")
        self.hit_sound = arcade.load_sound(":resources:sounds/hit3.wav")

    def setup(self):
        """ Настройка игры и переменных """
        self.window.background_color = arcade.color.AMAZON
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.score = 0

        # Инициализация сцены
        self.scene = arcade.Scene()

        # Создаем списки спрайтов в сцене
        self.scene.add_sprite_list("Player")
        self.scene.add_sprite_list("Walls")
        self.scene.add_sprite_list("Enemies")
        self.scene.add_sprite_list("Bullets")

        # --- Создание Игрока ---
        self.player = Player()
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = 100
        self.scene.add_sprite("Player", self.player)

        # --- Создание Врага (Тестовый) ---
        enemy = arcade.Sprite(RESOURCE_ENEMY, scale=PLAYER_SCALE)
        enemy.center_x = SCREEN_WIDTH // 2
        enemy.center_y = SCREEN_HEIGHT // 2
        self.scene.add_sprite("Enemies", enemy)

        # --- Создание Карты (Стены по периметру) ---
        # В будущем этот блок заменится на загрузку из Tiled
        for x in range(0, SCREEN_WIDTH, 64):
            # Нижняя стена
            wall = arcade.Sprite(RESOURCE_WALL, 0.5)
            wall.center_x = x
            wall.center_y = 32
            self.scene.add_sprite("Walls", wall)
            # Верхняя стена
            wall = arcade.Sprite(RESOURCE_WALL, 0.5)
            wall.center_x = x
            wall.center_y = SCREEN_HEIGHT - 32
            self.scene.add_sprite("Walls", wall)

        for y in range(64, SCREEN_HEIGHT - 32, 64):
            # Левая стена
            wall = arcade.Sprite(RESOURCE_WALL, 0.5)
            wall.center_x = 32
            wall.center_y = y
            self.scene.add_sprite("Walls", wall)
            # Правая стена
            wall = arcade.Sprite(RESOURCE_WALL, 0.5)
            wall.center_x = SCREEN_WIDTH - 32
            wall.center_y = y
            self.scene.add_sprite("Walls", wall)

        # --- Физика ---
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, self.scene["Walls"]
        )

    def on_draw(self):
        """ Рендеринг """
        self.clear()

        # Активируем камеру игрового мира
        self.camera.use()
        self.scene.draw()

        # Активируем камеру интерфейса (GUI) - остается неподвижной
        self.gui_camera.use()
        arcade.draw_text(f"Счет: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 14)

    def on_update(self, delta_time):
        # Движение игрока и физика
        self.physics_engine.update()

        # Обновление анимаций (пока максимально упрощенно)
        self.scene.update_animation(delta_time, ["Player"])
        enemy_touch = arcade.check_for_collision_with_list(self.player, self.scene["Enemies"])
        if enemy_touch:
            game_over = GameOverView(self.score)
            self.window.show_view(game_over)

        # Движение пуль
        self.scene.update(names=["Bullets"], delta_time=delta_time)

        # Проверка попаданий пуль во врагов
        for bullet in self.scene["Bullets"]:
            # Проверяем коллизии пули с врагами
            hit_list = arcade.check_for_collision_with_list(bullet, self.scene["Enemies"])

            # Проверяем коллизии пули со стенами (удаляем пулю)
            wall_hit_list = arcade.check_for_collision_with_list(bullet, self.scene["Walls"])

            if hit_list:
                bullet.remove_from_sprite_lists()
                for enemy in hit_list:
                    enemy.remove_from_sprite_lists()  # Убиваем врага
                    self.score += 100  # Начисляем очки
                    arcade.play_sound(self.hit_sound)

                    # Проверка условия победы (для теста: если врагов нет - конец игры)
                    if len(self.scene["Enemies"]) == 0:
                        game_over = GameOverView(self.score)
                        self.window.show_view(game_over)

            if wall_hit_list:
                bullet.remove_from_sprite_lists()

            # Удаляем пулю, если она улетела за экран (навсякий случай)
            if (bullet.center_x < 0 or bullet.center_x > SCREEN_WIDTH or
                    bullet.center_y < 0 or bullet.center_y > SCREEN_HEIGHT):
                bullet.remove_from_sprite_lists()

    def on_key_press(self, key, modifiers):
        """ Нажатие клавиш """
        if key == arcade.key.W or key == arcade.key.UP:
            self.player.change_y = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.player.change_y = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.ESCAPE:
            # Пауза или выход в меню
            menu = MainMenu()
            self.window.show_view(menu)

    def on_key_release(self, key, modifiers):
        """ Отпускание клавиш """
        if key == arcade.key.W or key == arcade.key.UP:
            self.player.change_y = 0
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.player.change_y = 0
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.player.change_x = 0
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.player.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        """ Стрельба по клику """
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Создаем пулю
            bullet = arcade.Sprite(RESOURCE_BULLET, BULLET_SCALE)
            bullet.center_x = self.player.center_x
            bullet.center_y = self.player.center_y

            # Вычисляем угол стрельбы
            start_x = self.player.center_x
            start_y = self.player.center_y

            dest_x = x
            dest_y = y

            # Математика вектора направления
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)

            # Поворачиваем спрайт пули
            bullet.angle = math.degrees(angle)

            # Задаем скорость пули
            bullet.change_x = math.cos(angle) * BULLET_SPEED
            bullet.change_y = math.sin(angle) * BULLET_SPEED

            self.scene.add_sprite("Bullets", bullet)
            arcade.play_sound(self.shoot_sound)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
