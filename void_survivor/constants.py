"""Game constants and configuration."""

# Window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TITLE = "Void Survivor"

# Colors
COLORS = {
    "background": (10, 10, 20),
    "grid": (20, 20, 40),
    "player": (100, 200, 255),
    "player_outline": (50, 150, 200),
    "health_bar": (50, 255, 50),
    "health_bar_bg": (40, 20, 20),
    "health_bar_damage": (255, 50, 50),
    "xp_bar": (150, 100, 255),
    "xp_bar_bg": (30, 20, 50),
    "enemy_basic": (255, 80, 80),
    "enemy_fast": (255, 220, 50),
    "enemy_tank": (180, 80, 255),
    "bullet": (100, 255, 200),
    "xp_orb": (150, 100, 255),
    "text": (255, 255, 255),
    "text_dim": (150, 150, 150),
    "upgrade_bg": (30, 30, 50),
    "upgrade_border": (80, 80, 120),
    "upgrade_hover": (50, 50, 80),
    "wave_text": (255, 200, 100),
    "game_over": (200, 30, 30),
}

# Player
PLAYER_RADIUS = 18
PLAYER_SPEED = 280
PLAYER_MAX_HEALTH = 120
PLAYER_INVINCIBILITY_TIME = 1.0
PLAYER_KNOCKBACK = 350

# Bullets
BULLET_SPEED = 650
BULLET_RADIUS = 5
BULLET_DAMAGE = 20
BULLET_LIFETIME = 1.5
BULLET_COOLDOWN = 0.3
BULLET_PIERCE = 1

# Enemies - Basic
ENEMY_BASIC_SPEED = 85
ENEMY_BASIC_HEALTH = 30
ENEMY_BASIC_RADIUS = 15
ENEMY_BASIC_DAMAGE = 8
ENEMY_BASIC_XP = 5

# Enemies - Fast
ENEMY_FAST_SPEED = 150
ENEMY_FAST_HEALTH = 15
ENEMY_FAST_RADIUS = 10
ENEMY_FAST_DAMAGE = 5
ENEMY_FAST_XP = 3

# Enemies - Tank
ENEMY_TANK_SPEED = 50
ENEMY_TANK_HEALTH = 80
ENEMY_TANK_RADIUS = 22
ENEMY_TANK_DAMAGE = 14
ENEMY_TANK_XP = 15

# XP
XP_ORB_RADIUS = 6
XP_ATTRACT_RADIUS = 150
XP_ATTRACT_SPEED = 400
XP_BASE_TO_NEXT = 30
XP_LEVEL_MULTIPLIER = 1.4

# Spawning
SPAWN_MARGIN = 100
BASE_SPAWN_INTERVAL = 3.5
MIN_SPAWN_INTERVAL = 1.5
MAX_ENEMIES = 60

# Particles
PARTICLE_COUNT = 8
PARTICLE_SPEED = 150
PARTICLE_LIFETIME = 0.5

# Upgrades
UPGRADE_CHOICES = 3
