import arcade
import arcade.gui
import math
import sqlite3
from constants import *
from effects import EffectManager
from entities import Player, Enemy, EnemyBullet, AcidPuddle


class GameView(arcade.View):
    def __init__(self, current_level_index=0, total_score=0):
        super().__init__()
        self.current_level_index = current_level_index
        self.total_score = total_score

        #Спрайт листы
        self.scene = None
        self.player = None
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None
        self.effect_manager = EffectManager()
        self.time = 0

        #Игровая статистика уровня
        self.level_score = 0
        self.coins_collected = 0
        self.level_start_time = 0

        #Звуки
        self.hit_sound = arcade.load_sound(":resources:sounds/hit3.wav")
        self.shoot_sound = arcade.load_sound(":resources:sounds/laser1.wav")
        self.secret_sound = arcade.load_sound(":resources:sounds/upgrade2.wav")

    def setup(self):
        #Настройка уровня
        self.window.background_color = arcade.color.BLACK
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        map_name = LEVEL_MAPS[self.current_level_index]
        self.all_killed = False
        self.scale = 4

        #Загрузка карты

        try:
            tile_map = arcade.load_tilemap(map_name, scaling=self.scale, use_spatial_hash=True)
            self.map_width = tile_map.width
            self.map_height = tile_map.height
            self.tile_size = 8 * self.scale

            self.scene = arcade.Scene.from_tilemap(tile_map)
        except Exception as e:
            print(f"Ошибка загрузки карты {map_name}: {e}")
            print("Убедитесь, что файл существует и слои названы верно.")
            return

        #Инициализация списков, если их нет в карте
        if "Bullets" not in self.scene:
            self.scene.add_sprite_list("Bullets")
        if "EnemyBullets" not in self.scene:
            self.scene.add_sprite_list("EnemyBullets")
        if "Puddles" not in self.scene:
            self.scene.add_sprite_list("Puddles")
        if "KEYS" not in self.scene:
            self.scene.add_sprite_list('Keys')
        if 'Coins' not in self.scene:
            self.scene.add_sprite_list('Coins')

        #Спавн Игрока
        # Ищем объект на слое спавна
        spawn_points = self.scene.get_sprite_list(LAYER_SPAWN)
        if spawn_points:
            start_pos = spawn_points[0]
            self.player = Player()
            self.player.center_x = start_pos.center_x
            self.player.center_y = start_pos.center_y
            self.scene.add_sprite("Player", self.player)

        else:
            self.player = Player()
            self.player.center_x = 100
            self.player.center_y = 100
            self.scene.add_sprite("Player", self.player)

        # Превращение тайлов врагов в умных Врагов
        if LAYER_ENEMIES in self.scene:
            enemy_markers = self.scene.get_sprite_list(LAYER_ENEMIES)
            for marker in enemy_markers:
                enemy = Enemy()
                enemy.center_x = marker.center_x
                enemy.center_y = marker.center_y
                self.scene.add_sprite("Enemies", enemy)

        #Физика
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, [self.scene.get_sprite_list(LAYER_WALLS)]
        )
        self.camera.position = self.player.position

    def on_draw(self):
        self.clear()
        self.camera.use()
        if self.scene:
            self.scene.draw()
        self.effect_manager.draw()

        self.gui_camera.use()

        #Инфо панель

        if not self.player:
            return
        score_text = f"Очки: {self.total_score + self.level_score}"
        coins_text = f"Звезды: {self.coins_collected}/3"
        key_text = "КЛЮЧ: ЕСТЬ" if self.player.has_key else "КЛЮЧ: НЕТ"
        hp_text = f"HP: {int(self.player.hp)}"

        arcade.draw_text(score_text, 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 14)
        arcade.draw_text(coins_text, 10, SCREEN_HEIGHT - 50, arcade.color.YELLOW, 14)
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

        #Физика игрока
        self.physics_engine.update()
        self.scene.update_animation(delta_time, ["Player", "Enemies"])
        self.scene.update(delta_time, ["Bullets", "EnemyBullets", "Puddles"])
        self.effect_manager.update(delta_time)

        #Камера следит за игроком
        self.cam_target = arcade.math.lerp_2d(self.camera.position, self.player.position, 0.3)

        # Ограничиваем движение по X
        x = max(self.cam_target[0], SCREEN_WIDTH // 2)
        x = min(x, self.map_width * self.tile_size - SCREEN_WIDTH // 2)

        # Ограничиваем движение по Y
        y = max(self.cam_target[1], SCREEN_HEIGHT // 2)
        y = min(y, self.map_height * self.tile_size - SCREEN_HEIGHT // 2)

        # Устанавливаем новую позицию камеры
        self.camera.position = (x, y)

        # Логика врагов и видимости
        if "Enemies" in self.scene:
            walls = self.scene.get_sprite_list(LAYER_WALLS)
            for enemy in self.scene.get_sprite_list("Enemies"):
                #Враг виден только если есть линия видимости
                enemy.visible = arcade.has_line_of_sight(self.player.position, enemy.position, walls)
                if enemy.follow_player(self.player, walls):
                    bullet = EnemyBullet(enemy.center_x, enemy.center_y, self.player.center_x, self.player.center_y)
                    self.scene.add_sprite("EnemyBullets", bullet)
                    arcade.play_sound(self.shoot_sound)

        #Обработка пуль Игрока
        for bullet in self.scene.get_sprite_list("Bullets"):
            #Попадание во врагов
            hit_enemies = arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list("Enemies"))
            if hit_enemies:
                bullet.remove_from_sprite_lists()
                for enemy in hit_enemies:
                    enemy.flash_red()
                    self.effect_manager.add_damage_effect(enemy.center_x, enemy.center_y)
                    enemy.hp -= 10  #Урон врагу
                    if enemy.hp <= 0:
                        #Смерть врага
                        puddle = AcidPuddle(enemy.center_x, enemy.center_y)
                        self.scene.add_sprite("Puddles", puddle)
                        enemy.remove_from_sprite_lists()
                        self.level_score += SCORE_ENEMY_KILL
                        arcade.play_sound(self.hit_sound)

            #Попадание в стены
            if arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list(LAYER_WALLS)):
                bullet.remove_from_sprite_lists()

        if not self.scene.get_sprite_list("Enemies") and not self.all_killed:
            self.level_score += SCORE_ALL_KILLED
            self.all_killed = True

        #Обработка пуль Врагов
        for bullet in self.scene.get_sprite_list("EnemyBullets"):
            #Попадание в стены = Лужа
            if arcade.check_for_collision_with_list(bullet, self.scene.get_sprite_list(LAYER_WALLS)):
                puddle = AcidPuddle(bullet.center_x, bullet.center_y, size=45)
                self.scene.add_sprite("Puddles", puddle)
                bullet.remove_from_sprite_lists()

            #Попадание в игрока
            if arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list("EnemyBullets")):
                self.player.hp -= 10
                puddle = AcidPuddle(bullet.center_x, bullet.center_y)
                self.scene.add_sprite("Puddles", puddle)
                bullet.remove_from_sprite_lists()

        #Обработка луж
        for puddle in self.scene.get_sprite_list("Puddles"):
            if puddle.is_expired():
                puddle.remove_from_sprite_lists()
            elif arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list("Puddles")):
                self.player.hp -= PUDDLE_DAMAGE * delta_time * 10  # Урон от кислоты

        #Исчезновение стен
        if LAYER_SECRETS in self.scene:
            secrets_hit = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_SECRETS))
            if secrets_hit:
                self.level_score += SCORE_SECRET_FOUND
                arcade.play_sound(self.secret_sound)
                self.scene.remove_sprite_list_by_name(LAYER_SECRETS)

        #Сбор предметов
        if LAYER_KEYS in self.scene:
            keys = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_KEYS))
            for key in keys:
                key.remove_from_sprite_lists()
                self.player.has_key = True
                arcade.play_sound(self.secret_sound)

        if LAYER_COINS in self.scene:
            coins = arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_COINS))
            for coin in coins:
                self.effect_manager.coin_effect(coin.center_x, coin.center_y)
                coin.remove_from_sprite_lists()
                self.coins_collected += 1
                self.level_score += SCORE_COIN_FOUND
                arcade.play_sound(self.secret_sound)

        #Выход с уровня
        if LAYER_EXIT in self.scene:
            if arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_EXIT)):
                if self.player.has_key:
                    self.next_level()
                else:
                    print('нужен ключ!')

        #Смерть игрока
        if self.player.hp <= 0:
            total = self.total_score + self.level_score
            view = GameOverView(total, "ВЫ ПОГИБЛИ")
            self.window.show_view(view)

    def next_level(self):
        total = self.total_score + self.level_score
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM levels WHERE id = ?', (str(self.current_level_index + 1)))
        cursor.execute('''INSERT INTO levels (id, coins, score) VALUES (?, ?, ?)''',
                       (self.current_level_index + 1, self.coins_collected, self.level_score))
        conn.commit()
        conn.close()

        if self.current_level_index < len(LEVEL_MAPS) - 1:
            next_view = GameView(self.current_level_index + 1, self.total_score)
            next_view.setup()
            self.window.show_view(next_view)
        else:
            view = GameOverView(total, f"ПОБЕДА! Монет: {self.coins_collected}")
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
    def __init__(self):
        super().__init__()
        self.ui_manager = arcade.gui.UIManager()
        self.level_buttons = []
        self.load_level_data()

    def load_level_data(self):
        #БАЗА ДАНЫХ
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT * FROM levels")
        self.levels = self.cursor.fetchall()

    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_BLUE_GRAY
        self.setup_ui()
        self.ui_manager.enable()

    def setup_ui(self):
        self.ui_manager.clear()

        root = arcade.gui.UIAnchorLayout(anchor_x="center", anchor_y="center")

        main_box = arcade.gui.UIBoxLayout(spacing=20)

        title = arcade.gui.UILabel(
            text="MAZE SHOOTER",
            font_size=50,
            align="center",
            width=self.window.width
        )
        main_box.add(title)

        levels_box = arcade.gui.UIBoxLayout(spacing=10)

        for level in self.levels:
            level_id, coins, score = level

            button = arcade.gui.UIFlatButton(
                text=f"Уровень {level_id}",
                width=200,
                height=50,
            )

            stats = arcade.gui.UILabel(
                text=f"Монеты: {coins} | Очки: {score}",
                font_size=14,
                width=200,
                align="center"
            )

            level_widget = arcade.gui.UIBoxLayout(spacing=5)
            level_widget.add(button)
            level_widget.add(stats)

            button.on_click = lambda event, id=level_id: self.start_level(id)

            levels_box.add(level_widget)
            self.level_buttons.append(button)

        main_box.add(levels_box)

        exit_button = arcade.gui.UIFlatButton(
            text="Выход",
            width=200,
            height=50,
        )
        exit_button.on_click = self.close_game
        main_box.add(exit_button)

        root.add(main_box)

        self.ui_manager.add(root)
        self.ui_manager.enable()

    def start_level(self, level_id):
        game_view = GameView(current_level_index=level_id - 1)
        game_view.setup()
        self.ui_manager.disable()
        self.window.show_view(game_view)

    def close_game(self, event):
        arcade.close_window()

    def on_draw(self):
        self.clear()
        self.ui_manager.draw()

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