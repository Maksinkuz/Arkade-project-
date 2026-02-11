#Размеры окна
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_TITLE = "Maze Shooter"

#Размеры мёртвой зоны камеры
DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35)
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.45)

#Спрайты
RESOURCE_PLAYER = ":resources:/images/animated_characters/robot/robot_idle.png"
RESOURCE_PLAYER_WALK = [f":resources:/images/animated_characters/robot/robot_walk{i}.png" for i in range(7)]
RESOURCE_ENEMY = ":resources:images/animated_characters/zombie/zombie_idle.png"
RESOURCE_ENEMY_WALK = [f":resources:/images/animated_characters/zombie/zombie_walk{i}.png" for i in range(7)]
RESOURCE_WALL = ":resources:images/tiles/boxCrate_double.png"
RESOURCE_BULLET = ":resources:images/space_shooter/laserBlue01.png"

#Параметры игрока
PLAYER_SCALE = 0.5
PLAYER_SPEED = 10
PLAYER_START_HP = 300

#Параметры врагов
ENEMY_SCALE = 0.5
ENEMY_SPEED = 3
ENEMY_SIGHT_DISTANCE = 400  # Дистанция, с которой враг видит игрока
ENEMY_ATTACK_COOLDOWN = 3.0 # Секунды между выстрелами

#Параметры снарядов и луж
BULLET_SPEED = 7
PUDDLE_LIFE_TIME = 5.0  #Сколько секунд живет лужа
PUDDLE_DAMAGE = 1       #Урон от лужи в тик

# --- Очки ---
SCORE_ENEMY_KILL = 100
SCORE_SECRET_FOUND = 350
SCORE_COIN_FOUND = 200
SCORE_ALL_KILLED = 1000

#Названия слоев в Tiled
LAYER_WALLS = "collisions"
LAYER_ENEMIES = "enemies"      #Слой тайлов,где стоят враги
LAYER_SECRETS = "secret"       #Слой крыш секретных комнат
LAYER_KEYS = "keys"           #Ключи
LAYER_COINS = "coins"          #Звезды
LAYER_EXIT = "exit"            #Зона выхода
LAYER_SPAWN = "spawn_point"    #Точка старта игрока

#Пути к картам
LEVEL_MAPS = ["maps/lvl1.tmx", "maps/lvl2.tmx"]
DB_NAME = "gamedata.db"