import arcade
import math
import time
from constants import *


class Entity(arcade.Sprite):

    def __init__(self, filename, scale):
        super().__init__(filename, scale=scale)
        self.hit_timer = 0

    def flash_red(self):
        #Визуальный эффект получения урона
        self.color = arcade.color.RED
        self.hit_timer = 0.1  # Длительность вспышки

    def update_effects(self, delta_time):
        if self.hit_timer > 0:
            self.hit_timer -= delta_time
            if self.hit_timer <= 0:
                self.color = arcade.color.WHITE

    def update(self, delta_time: float = 1 / 60):
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

class Player(Entity):
    def __init__(self):
        super().__init__(RESOURCE_PLAYER, PLAYER_SCALE)
        self.hp = PLAYER_START_HP
        self.has_key = False
        self.idle_texture = arcade.load_texture(RESOURCE_PLAYER)
        self.walk_textures = [arcade.load_texture(t) for t in RESOURCE_PLAYER_WALK]

        self.anim_timer = 0
        self.current_frame = 0
        self.texture = self.idle_texture

    def update_animation(self, delta_time: float = 1 / 60):
        self.update_effects(delta_time)

        #Проверяем, движется ли игрок
        if abs(self.change_x) > 0.1 or abs(self.change_y) > 0.1:
            self.anim_timer += delta_time
            if self.anim_timer > 0.1:  #Скорость смены кадров
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_textures)

                #Поворот
                base_texture = self.walk_textures[self.current_frame]
                if self.change_x < 0:
                    self.texture = base_texture.flip_left_right()
                else:
                    self.texture = base_texture
        else:
            self.texture = self.idle_texture

class Enemy(Entity):
    def __init__(self):
        super().__init__(RESOURCE_ENEMY, ENEMY_SCALE)
        self.hp = 30
        self.last_shot_time = 0
        self.idle_texture = arcade.load_texture(RESOURCE_ENEMY)
        self.walk_textures = [arcade.load_texture(t) for t in RESOURCE_ENEMY_WALK]

        self.anim_timer = 0
        self.current_frame = 0
        self.texture = self.idle_texture

    def follow_player(self, player_sprite, wall_list):
        distance = arcade.get_distance_between_sprites(self, player_sprite)
        has_los = arcade.has_line_of_sight(self.position, player_sprite.position, wall_list)

        if distance < ENEMY_SIGHT_DISTANCE and has_los:
            x_diff = player_sprite.center_x - self.center_x
            y_diff = player_sprite.center_y - self.center_y
            angle = math.atan2(y_diff, x_diff)

            self.change_x = math.cos(angle) * ENEMY_SPEED
            self.change_y = math.sin(angle) * ENEMY_SPEED

            self.center_x += self.change_x
            self.center_y += self.change_y

            if time.time() - self.last_shot_time > ENEMY_ATTACK_COOLDOWN:
                self.last_shot_time = time.time()
                return True
        else:
            self.change_x = 0
            self.change_y = 0

        return False

    def update_animation(self, delta_time: float = 1 / 60):
        self.update_effects(delta_time)
        if abs(self.change_x) > 0.1 or abs(self.change_y) > 0.1:
            self.anim_timer += delta_time
            if self.anim_timer > 0.1:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_textures)

                base_tex = self.walk_textures[self.current_frame]
                self.texture = base_tex.flip_left_right() if self.change_x < 0 else base_tex
        else:
            self.texture = self.idle_texture



class AcidPuddle(arcade.Sprite):
    #ядовитые лужи

    def __init__(self, x, y, size=20):
        super().__init__(scale=1.0)
        self.texture = arcade.make_circle_texture(size, arcade.color.BRIGHT_GREEN)
        self.center_x = x
        self.center_y = y
        self.creation_time = time.time()

    def is_expired(self):
        #Проверка исчезла ли лужа
        return time.time() - self.creation_time > PUDDLE_LIFE_TIME


class EnemyBullet(arcade.Sprite):
    #Пуля врага

    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__(scale=1.0)
        self.texture = arcade.make_circle_texture(7, arcade.color.BRIGHT_GREEN)
        self.center_x = start_x
        self.center_y = start_y

        #Расчет вектора движения
        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)

        self.change_x = math.cos(angle) * BULLET_SPEED
        self.change_y = math.sin(angle) * BULLET_SPEED


