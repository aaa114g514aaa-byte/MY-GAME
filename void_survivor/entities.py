"""Game entities: Player, Enemy, Bullet, XPOrb, Particle."""

import math
import random
import pygame

from constants import *


class Player:
    def __init__(self):
        self.x = WINDOW_WIDTH / 2
        self.y = WINDOW_HEIGHT / 2
        self.radius = PLAYER_RADIUS
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.level = 1
        self.xp = 0
        self.xp_to_next = XP_BASE_TO_NEXT
        self.shoot_cooldown = 0
        self.invincible_timer = 0
        self.alive = True

        # Stats (modified by upgrades)
        self.damage = BULLET_DAMAGE
        self.fire_rate = BULLET_COOLDOWN
        self.bullet_speed = BULLET_SPEED
        self.bullet_size = BULLET_RADIUS
        self.pierce = BULLET_PIERCE
        self.move_speed = PLAYER_SPEED

        self.angle = 0.0

    def update(self, dt):
        if not self.alive:
            return

        dx, dy = 0.0, 0.0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.angle = math.atan2(dy, dx)

        self.x += dx * self.move_speed * dt
        self.y += dy * self.move_speed * dt

        # Clamp to screen
        self.x = max(self.radius, min(WINDOW_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(WINDOW_HEIGHT - self.radius, self.y))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    def take_damage(self, amount):
        if self.invincible_timer > 0:
            return False
        self.health -= amount
        self.invincible_timer = PLAYER_INVINCIBILITY_TIME
        if self.health <= 0:
            self.health = 0
            self.alive = False
        return True

    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(XP_BASE_TO_NEXT * (XP_LEVEL_MULTIPLIER ** (self.level - 1)))
            return True
        return False

    def can_shoot(self):
        return self.alive and self.shoot_cooldown <= 0

    def shoot(self):
        self.shoot_cooldown = self.fire_rate


class Enemy:
    def __init__(self, x, y, enemy_type="basic"):
        self.x = x
        self.y = y
        self.type = enemy_type

        if enemy_type == "basic":
            self.radius = ENEMY_BASIC_RADIUS
            self.speed = ENEMY_BASIC_SPEED
            self.health = ENEMY_BASIC_HEALTH
            self.max_health = ENEMY_BASIC_HEALTH
            self.damage = ENEMY_BASIC_DAMAGE
            self.xp_value = ENEMY_BASIC_XP
            self.color = COLORS["enemy_basic"]
        elif enemy_type == "fast":
            self.radius = ENEMY_FAST_RADIUS
            self.speed = ENEMY_FAST_SPEED
            self.health = ENEMY_FAST_HEALTH
            self.max_health = ENEMY_FAST_HEALTH
            self.damage = ENEMY_FAST_DAMAGE
            self.xp_value = ENEMY_FAST_XP
            self.color = COLORS["enemy_fast"]
        elif enemy_type == "tank":
            self.radius = ENEMY_TANK_RADIUS
            self.speed = ENEMY_TANK_SPEED
            self.health = ENEMY_TANK_HEALTH
            self.max_health = ENEMY_TANK_HEALTH
            self.damage = ENEMY_TANK_DAMAGE
            self.xp_value = ENEMY_TANK_XP
            self.color = COLORS["enemy_tank"]

        self.hit_flash_timer = 0.0

    def update(self, dt, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash_timer = 0.1
        return self.health <= 0


class Bullet:
    def __init__(self, x, y, angle, speed, damage, radius, pierce):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.damage = damage
        self.radius = radius
        self.lifetime = BULLET_LIFETIME
        self.pierce_remaining = pierce
        self.hit_enemies = []
        self.active = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
        if (
            self.x < -50 or self.x > WINDOW_WIDTH + 50
            or self.y < -50 or self.y > WINDOW_HEIGHT + 50
        ):
            self.active = False


class XPOrb:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.radius = XP_ORB_RADIUS
        self.active = True

    def update(self, dt, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist < XP_ATTRACT_RADIUS and dist > 1:
            speed = XP_ATTRACT_SPEED * (1.0 - dist / XP_ATTRACT_RADIUS)
            self.x += (dx / dist) * speed * dt
            self.y += (dy / dist) * speed * dt


class ParticleSystem:
    def __init__(self, x, y, color, count=None):
        if count is None:
            count = PARTICLE_COUNT
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, PARTICLE_SPEED)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "lifetime": random.uniform(0.2, PARTICLE_LIFETIME),
                "max_lifetime": PARTICLE_LIFETIME,
                "color": color,
                "radius": random.uniform(2, 4),
            })

    def update(self, dt):
        for p in self.particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["lifetime"] -= dt
            if p["lifetime"] <= 0:
                self.particles.remove(p)

    def is_dead(self):
        return len(self.particles) == 0
