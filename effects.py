import arcade
from random import randint, uniform
import math

class Particle(arcade.SpriteCircle):
    def __init__(self, x, y, color, change_x, change_y, fade_speed=5, gravity=0):
        super().__init__(radius=3, color=color)
        self.center_x = x
        self.center_y = y
        self.change_x = change_x
        self.change_y = change_y
        self.fade_speed = fade_speed
        self.gravity = gravity

    def update(self, delta_time):
        super().update()
        self.change_y -= self.gravity * delta_time
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        self.alpha -= self.fade_speed
        if self.alpha <= 0:
            self.remove_from_sprite_lists()

class EffectManager:
    def __init__(self):
        self.particles = arcade.SpriteList()

    def add_damage_effect(self, x, y):
        #Красные капельки
        for _ in range(randint(10, 15)):
            angle = uniform(0, 2 * math.pi)
            speed = uniform(2, 5)
            p = Particle(
                x, y,
                color=arcade.color.RED,
                change_x=math.cos(angle) * speed,
                change_y=math.sin(angle) * speed,
                fade_speed=7
            )
            self.particles.append(p)

    def coin_effect(self, x, y):
        for _ in range(randint(20, 25)):
            angle = uniform(math.pi * 0.3, math.pi * 0.7)
            speed = uniform(4, 8)
            p = Particle(
                x, y,
                color=arcade.color.GOLD,
                change_x=math.cos(angle) * speed,
                change_y=math.sin(angle) * speed,
                fade_speed=3,
                gravity=10
            )
            self.particles.append(p)

    def update(self, delta_time):
        self.particles.update(delta_time)

    def draw(self):
        self.particles.draw()