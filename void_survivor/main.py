"""Void Survivor — a Vampire-Survivors-like 2D game built with Pygame."""

import math
import random
import sys

import pygame

from constants import *
from entities import Player, Enemy, Bullet, XPOrb, ParticleSystem
from ui import *


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def nearest_enemy(px, py, enemies):
    best, best_d2 = None, float("inf")
    for e in enemies:
        dx, dy = e.x - px, e.y - py
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best = e
    return best


def make_enemy(wave):
    """Create a single enemy scaled by current wave."""
    pool = ["basic"]
    if wave >= 2:
        pool.append("fast")
    if wave >= 4:
        pool.append("tank")
    t = random.choice(pool)

    edge = random.randint(0, 3)
    if edge == 0:   # top
        x = random.uniform(0, WINDOW_WIDTH)
        y = -SPAWN_MARGIN
    elif edge == 1:  # bottom
        x = random.uniform(0, WINDOW_WIDTH)
        y = WINDOW_HEIGHT + SPAWN_MARGIN
    elif edge == 2:  # left
        x = -SPAWN_MARGIN
        y = random.uniform(0, WINDOW_HEIGHT)
    else:            # right
        x = WINDOW_WIDTH + SPAWN_MARGIN
        y = random.uniform(0, WINDOW_HEIGHT)

    e = Enemy(x, y, t)
    scale = 1.0 + wave * 0.07
    e.health *= scale
    e.max_health = e.health
    e.speed *= 1.0 + wave * 0.03
    e.damage *= 1.0 + wave * 0.05
    return e


# ---------------------------------------------------------------------------
# Upgrades
# ---------------------------------------------------------------------------

def _gen_upgrades():
    return [
        {"id": "damage",     "name": "Damage Up",     "description": "Bullet damage +50%",         "color": (255, 100, 50)},
        {"id": "fire_rate",  "name": "Fire Rate Up",  "description": "Shoot 30% faster",           "color": (255, 200, 50)},
        {"id": "speed",      "name": "Speed Up",      "description": "Move speed +20%",            "color": (100, 255, 100)},
        {"id": "max_health", "name": "Health Up",     "description": "Max health +25",             "color": (255, 50, 50)},
        {"id": "bullet_size","name": "Bullet Size Up","description": "Bullet size +40%",            "color": (100, 200, 255)},
        {"id": "pierce",     "name": "Pierce",        "description": "Bullets pierce +1 enemy",    "color": (255, 100, 200)},
    ]


def _apply_upgrade(player, uid):
    if uid == "damage":
        player.damage *= 1.5
    elif uid == "fire_rate":
        player.fire_rate *= 0.7
    elif uid == "speed":
        player.move_speed *= 1.2
    elif uid == "max_health":
        player.max_health += 25
        player.health = min(player.health + 25, player.max_health)
    elif uid == "bullet_size":
        player.bullet_size *= 1.4
    elif uid == "pierce":
        player.pierce += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # ---- state ----
    player = Player()
    enemies: list[Enemy] = []
    bullets: list[Bullet] = []
    xp_orbs: list[XPOrb] = []
    particles: list[ParticleSystem] = []

    score = 0
    wave = 1
    wave_timer = 3.0
    announce_timer = 0.0
    spawn_timer = 0.0
    state = "playing"  # playing | level_up | game_over
    upgrades = []
    shake = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.05:
            dt = 0.05  # cap for large frame gaps

        # ---- input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if event.key == pygame.K_SPACE and state == "game_over":
                    # restart
                    player = Player()
                    enemies.clear()
                    bullets.clear()
                    xp_orbs.clear()
                    particles.clear()
                    score = 0
                    wave = 1
                    wave_timer = 3.0
                    announce_timer = 0.0
                    spawn_timer = 0.0
                    state = "playing"
                    shake = 0.0

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "level_up":
                    mx, my = event.pos
                    for upg in upgrades:
                        r = upg.get("rect")
                        if r and r.collidepoint(mx, my):
                            _apply_upgrade(player, upg["id"])
                            state = "playing"
                            upgrades.clear()
                            break
                elif state == "game_over":
                    player = Player()
                    enemies.clear()
                    bullets.clear()
                    xp_orbs.clear()
                    particles.clear()
                    score = 0
                    wave = 1
                    wave_timer = 3.0
                    announce_timer = 0.0
                    spawn_timer = 0.0
                    state = "playing"
                    shake = 0.0

        if not running:
            break

        # ---- update ----
        if state == "playing":
            player.update(dt)

            # Auto-shoot at nearest enemy
            if player.can_shoot():
                target = nearest_enemy(player.x, player.y, enemies)
                if target:
                    angle = math.atan2(target.y - player.y, target.x - player.x)
                    b = Bullet(
                        player.x, player.y, angle,
                        player.bullet_speed, player.damage,
                        player.bullet_size, player.pierce,
                    )
                    bullets.append(b)
                    player.shoot()

            # Enemies
            for enemy in enemies[:]:
                enemy.update(dt, player.x, player.y)
                # collision with player
                dx = player.x - enemy.x
                dy = player.y - enemy.y
                dist = math.hypot(dx, dy)
                if dist < player.radius + enemy.radius:
                    if player.take_damage(enemy.damage):
                        shake = 8.0
                        particles.append(ParticleSystem(enemy.x, enemy.y, enemy.color, 4))

            # Bullets
            for bullet in bullets[:]:
                bullet.update(dt)
                if not bullet.active:
                    bullets.remove(bullet)
                    continue
                for enemy in enemies[:]:
                    if bullet in bullet.hit_enemies:
                        continue
                    dx = bullet.x - enemy.x
                    dy = bullet.y - enemy.y
                    if math.hypot(dx, dy) < bullet.radius + enemy.radius:
                        killed = enemy.take_damage(bullet.damage)
                        if killed:
                            xp_orbs.append(XPOrb(enemy.x, enemy.y, enemy.xp_value))
                            particles.append(ParticleSystem(enemy.x, enemy.y, enemy.color))
                            score += enemy.xp_value * 10
                            enemies.remove(enemy)
                            shake = max(shake, 3.0)
                        else:
                            particles.append(ParticleSystem(enemy.x, enemy.y, (255, 255, 200), 3))
                            shake = max(shake, 1.0)

                        bullet.hit_enemies.append(bullet)
                        if bullet.pierce_remaining <= 0:
                            bullet.active = False
                            bullets.remove(bullet)
                        else:
                            bullet.pierce_remaining -= 1
                            bullet.damage *= 0.8
                        break

            # XP orbs
            for orb in xp_orbs[:]:
                orb.update(dt, player.x, player.y)
                dx = player.x - orb.x
                dy = player.y - orb.y
                if math.hypot(dx, dy) < player.radius + orb.radius:
                    if player.add_xp(orb.value):
                        state = "level_up"
                        upgrades = random.sample(_gen_upgrades(), min(UPGRADE_CHOICES, 3))
                    xp_orbs.remove(orb)

            # Wave spawning
            wave_timer -= dt
            if wave_timer <= 0:
                count = min(2 + wave, 12)
                for _ in range(count):
                    if len(enemies) < MAX_ENEMIES:
                        enemies.append(make_enemy(wave))
                announce_timer = 3.0
                wave += 1
                wave_timer = max(MIN_SPAWN_INTERVAL, BASE_SPAWN_INTERVAL - wave * 0.08)

            # Continuous spawn (gentle trickle, not a flood)
            spawn_timer -= dt
            if spawn_timer <= 0:
                if len(enemies) < MAX_ENEMIES:
                    enemies.append(make_enemy(wave))
                spawn_timer = max(1.5, 3.5 - wave * 0.08)

            # Game over
            if not player.alive:
                state = "game_over"
                particles.append(ParticleSystem(player.x, player.y, COLORS["player"], 20))
                shake = 15.0

        # Particles always update
        for ps in particles[:]:
            ps.update(dt)
            if ps.is_dead():
                particles.remove(ps)

        shake *= 0.85
        if shake < 0.5:
            shake = 0.0

        if announce_timer > 0:
            announce_timer -= dt

        # ---- render ----
        off_x = random.uniform(-shake, shake) if shake > 0 else 0
        off_y = random.uniform(-shake, shake) if shake > 0 else 0

        screen.fill(COLORS["background"])
        draw_grid(screen)

        # World surface (for shake)
        world = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        # XP orbs
        for orb in xp_orbs:
            pygame.draw.circle(world, COLORS["xp_orb"], (int(orb.x), int(orb.y)), orb.radius)

        # Enemies
        for enemy in enemies:
            color = (255, 255, 255) if enemy.hit_flash_timer > 0 else enemy.color
            pygame.draw.circle(world, color, (int(enemy.x), int(enemy.y)), enemy.radius)
            if enemy.health < enemy.max_health:
                bw = enemy.radius * 2
                bh = 3
                bx = int(enemy.x - enemy.radius)
                by = int(enemy.y - enemy.radius - 8)
                pygame.draw.rect(world, (60, 20, 20), (bx, by, bw, bh))
                hw = int(bw * (enemy.health / enemy.max_health))
                if hw > 0:
                    pygame.draw.rect(world, (255, 80, 80), (bx, by, hw, bh))

        # Bullets
        for bullet in bullets:
            pygame.draw.circle(world, COLORS["bullet"], (int(bullet.x), int(bullet.y)), bullet.radius)
            # trail
            trail_x = int(bullet.x - bullet.vx * 0.02)
            trail_y = int(bullet.y - bullet.vy * 0.02)
            pygame.draw.circle(world, (*COLORS["bullet"][:3], 100), (trail_x, trail_y), bullet.radius * 0.7)

        # Player
        if player.alive:
            blink = player.invincible_timer <= 0 or int(player.invincible_timer * 10) % 2 == 0
            color = COLORS["player"] if blink else (255, 255, 255)
            pygame.draw.circle(world, color, (int(player.x), int(player.y)), player.radius)
            # direction dot
            dx = player.x + math.cos(player.angle) * player.radius
            dy = player.y + math.sin(player.angle) * player.radius
            pygame.draw.circle(world, COLORS["player_outline"], (int(dx), int(dy)), player.radius // 2)

        # Particles
        for ps in particles:
            for p in ps.particles:
                a = int(255 * (p["lifetime"] / p["max_lifetime"]))
                c = (*p["color"][:3], a)
                pygame.draw.circle(world, c, (int(p["x"]), int(p["y"])), p["radius"])

        screen.blit(world, (off_x, off_y))

        # UI (no shake)
        if state != "game_over":
            draw_health_bar(screen, player)
            draw_xp_bar(screen, player)
            draw_score(screen, score)
            draw_wave_announcement(screen, wave - 1, announce_timer)

        if state == "level_up":
            draw_upgrade_screen(screen, upgrades)
        elif state == "game_over":
            draw_game_over(screen, score, wave - 1)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
