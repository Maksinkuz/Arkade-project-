import arcade
import math
from constants import *
from entities import Player, Enemy, EnemyBullet, AcidPuddle


class GameView(arcade.View):
    def __init__(self, current_level_index=0, total_score=0):
        super().__init__()
        self.current_level_index = current_level_index
        self.total_score = total_score

        # Спрайт-листы
        self.scene = None
        self.player = None
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None
        self.time = 0

        # Игровая статистика уровня
        self.level_score = 0
        self.stars_collected = 0
        self.level_start_time = 0

        # Звуки
        self.hit_sound = arcade.load_sound(":resources:sounds/hit3.wav")
        self.shoot_sound = arcade.load_sound(":resources:sounds/laser1.wav")
        self.secret_sound = arcade.load_sound(":resources:sounds/upgrade2.wav")

    def setup(self):
        """ Настройка уровня """
        self.window.background_color = arcade.color.BLACK
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        map_name = LEVEL_MAPS[self.current_level_index]
        self.all_killed = False
        self.scale = 3.7

        # --- Загрузка карты ---

        try:
            tile_map = arcade.load_tilemap(map_name, scaling=self.scale, use_spatial_hash=True)
            self.map_width = tile_map.width
            self.map_height = tile_map.height

            self.scene = arcade.Scene.from_tilemap(tile_map)
        except Exception as e:
            print(f"Ошибка загрузки карты {map_name}: {e}")
            print("Убедитесь, что файл существует и слои названы верно.")
            return

        if "Bullets" not in self.scene:
            self.scene.add_sprite_list("Bullets")
        if "EnemyBullets" not in self.scene:
            self.scene.add_sprite_list("EnemyBullets")
        if "Puddles" not in self.scene:
            self.scene.add_sprite_list("Puddles")
        if "KEYS" not in self.scene:
            self.scene.add_sprite_list('Keys')
        if 'Stars' not in self.scene:
            self.scene.add_sprite_list('Stars')

        # --- Спавн Игрока ---
        spawn_points = self.scene.get_sprite_list(LAYER_SPAWN)
        if spawn_points:
            start_pos = spawn_points[0]
            self.player = Player()
            self.player.center_x = start_pos.center_x
            self.player.center_y = start_pos.center_y
            self.scene.add_sprite("Player", self.player)


        # --- Превращение тайлов врагов в умных Врагов ---
        if LAYER_ENEMIES in self.scene:
            enemy_markers = self.scene.get_sprite_list(LAYER_ENEMIES)
            for marker in enemy_markers:
                enemy = Enemy()
                enemy.center_x = marker.center_x
                enemy.center_y = marker.center_y
                self.scene.add_sprite("Enemies", enemy)

        # --- Физика ---
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, [self.scene.get_sprite_list(LAYER_WALLS)]
        )
        self.camera.position = self.camera.unproject(self.player.position)

    def on_draw(self):
        self.clear()
        self.camera.use()
        if self.scene:
            self.scene.draw()

        self.gui_camera.use()

        # Инфо панель

        if not self.player:
            return
        score_text = f"Очки: {self.total_score + self.level_score}"
        stars_text = f"Звезды: {self.stars_collected}/3"
        key_text = "КЛЮЧ: ЕСТЬ" if self.player.has_key else "КЛЮЧ: НЕТ"
        hp_text = f"HP: {int(self.player.hp)}"

        arcade.draw_text(score_text, 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 14)
        arcade.draw_text(stars_text, 10, SCREEN_HEIGHT - 50, arcade.color.YELLOW, 14)
        arcade.draw_text(key_text, 10, SCREEN_HEIGHT - 70, arcade.color.CYAN, 14)
        arcade.draw_text(hp_text, 10, SCREEN_HEIGHT - 90,
                         arcade.color.RED if self.player.hp < 30 else arcade.color.GREEN, 14)

    def on_update(self, delta_time):
        if not self.scene:
            return
        self.time += delta_time
        if self.time > 0.25:
            self.level_score = max(0, self.level_score - 1)
            self.time = 0

        # 1. Физика игрока
        self.physics_engine.update()
        self.scene.update(delta_time, ["Bullets", "EnemyBullets", "Puddles"])

        # 2. Камера следит за игроком
        self.camera.position = self.player.position

        # 3. Логика врагов
        if "Enemies" in self.scene:
            walls = self.scene.get_sprite_list(LAYER_WALLS)
            for enemy in self.scene.get_sprite_list("Enemies"):
                # ИИ преследования
                should_shoot = enemy.follow_player(self.player, walls)

                if should_shoot:
                    bullet = EnemyBullet(enemy.center_x, enemy.center_y,
                                         self.player.center_x, self.player.center_y)
                    self.scene.add_sprite("EnemyBullets", bullet)
                    arcade.play_sound(self.shoot_sound)

        # 5. Обработка пуль Игрока
        for bullet in self.scene.get_sprite_list("Bullets"):
            # Попадание во врагов
            hit_enemies = arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list("Enemies"))
            if hit_enemies:
                bullet.remove_from_sprite_lists()
                for enemy in hit_enemies:
                    enemy.hp -= 10  # Урон врагу
                    if enemy.hp <= 0:
                        # Смерть врага
                        puddle = AcidPuddle(enemy.center_x, enemy.center_y)
                        self.scene.add_sprite("Puddles", puddle)
                        enemy.remove_from_sprite_lists()
                        self.level_score += SCORE_ENEMY_KILL
                        arcade.play_sound(self.hit_sound)

            # Попадание в стены
            if arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list(LAYER_WALLS)):
                bullet.remove_from_sprite_lists()

        if not self.scene.get_sprite_list("Enemies") and not self.all_killed:
            self.level_score += SCORE_ALL_KILLED
            self.all_killed = True

        # 6. Обработка пуль Врагов (Ядовитый шарик)
        for bullet in self.scene.get_sprite_list("EnemyBullets"):
            # Попадание в стены -> Лужа
            if arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list(LAYER_WALLS)):
                puddle = AcidPuddle(bullet.center_x, bullet.center_y, size=45)
                self.scene.add_sprite("Puddles", puddle)
                bullet.remove_from_sprite_lists()

            # Попадание в игрока
            if arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list("EnemyBullets")):
                self.player.hp -= 10
                puddle = AcidPuddle(bullet.center_x, bullet.center_y)
                self.scene.add_sprite("Puddles", puddle)
                bullet.remove_from_sprite_lists()

        # 7. Обработка луж
        for puddle in self.scene.get_sprite_list("Puddles"):
            if puddle.is_expired():
                puddle.remove_from_sprite_lists()
            elif arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list("Puddles")):
                self.player.hp -= PUDDLE_DAMAGE * delta_time * 10  # Урон от кислоты

        # 8. Секреты (Исчезновение стен)
        if LAYER_SECRETS in self.scene:
            secrets_hit = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_SECRETS))
            if secrets_hit:
                self.level_score += SCORE_SECRET_FOUND
                arcade.play_sound(self.secret_sound)
                self.scene.remove_sprite_list_by_name(LAYER_SECRETS)

        # 9. Сбор предметов
        if LAYER_KEYS in self.scene:
            keys = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_KEYS))
            for key in keys:
                key.remove_from_sprite_lists()
                self.player.has_key = True
                arcade.play_sound(self.secret_sound)

        if LAYER_STARS in self.scene:
            stars = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_STARS))
            for star in stars:
                star.remove_from_sprite_lists()
                self.stars_collected += 1
                self.level_score += SCORE_STAR_FOUND
                arcade.play_sound(self.secret_sound)

        # 10. Выход с уровня
        if LAYER_EXIT in self.scene:
            if arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_EXIT)):
                if self.player.has_key:
                    self.next_level()
                else:
                    print('нужен ключ!')

        # 11. Смерть игрока
        if self.player.hp <= 0:
            total = self.total_score + self.level_score
            view = GameOverView(total, "ВЫ ПОГИБЛИ")
            self.window.show_view(view)

    def next_level(self):
        total = self.total_score + self.level_score

        # Переход
        if self.current_level_index < len(LEVEL_MAPS) - 1:
            next_view = GameView(self.current_level_index + 1, self.total_score)
            next_view.setup()
            self.window.show_view(next_view)
        else:
            view = GameOverView(total, f"ПОБЕДА! Звезд: {self.stars_collected}")
            self.window.show_view(view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.player.change_y = PLAYER_SPEED
        elif key == arcade.key.S:
            self.player.change_y = -PLAYER_SPEED
        elif key == arcade.key.A:
            self.player.change_x = -PLAYER_SPEED
        elif key == arcade.key.D:
            self.player.change_x = PLAYER_SPEED
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MainMenu())

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.S]:
            self.player.change_y = 0
        elif key in [arcade.key.A, arcade.key.D]:
            self.player.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Создаем пулю игрока
            world_coordinates = self.camera.unproject((x, y))
            real_x, real_y = world_coordinates.x, world_coordinates.y

            bullet = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png", 0.5)
            bullet.center_x = self.player.center_x
            bullet.center_y = self.player.center_y

            x_diff = real_x - bullet.center_x
            y_diff = real_y - bullet.center_y
            angle = math.atan2(y_diff, x_diff)

            bullet.change_x = math.cos(angle) * BULLET_SPEED * 1.5
            bullet.change_y = math.sin(angle) * BULLET_SPEED * 1.5
            bullet.angle = math.degrees(-angle)

            self.scene.add_sprite("Bullets", bullet)
            arcade.play_sound(self.shoot_sound)


class MainMenu(arcade.View):
    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_BLUE_GRAY

    def on_draw(self):
        self.clear()
        arcade.draw_text("MAZE SHOOTER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("Нажмите ENTER, чтобы начать", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
                         arcade.color.GRAY, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)

class GameOverView(arcade.View):
    def __init__(self, score, message="ИГРА ОКОНЧЕНА"):
        super().__init__()
        self.score = score
        self.message = message

    def on_show_view(self):
        self.window.background_color = arcade.color.BLACK

    def on_draw(self):
        self.clear()
        arcade.draw_text(self.message, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.RED, font_size=40, anchor_x="center")
        arcade.draw_text(f"Итоговый счет: {self.score}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, font_size=30, anchor_x="center")
        arcade.draw_text("ENTER - Меню", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60,
                         arcade.color.GRAY, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            menu = MainMenu()
            self.window.show_view(menu)