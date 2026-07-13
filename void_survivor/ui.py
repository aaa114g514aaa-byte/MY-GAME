"""UI rendering: HUD, menus, effects."""

import pygame

from constants import *


def draw_health_bar(screen, player):
    bar_width = 250
    bar_height = 20
    x, y = 20, 20

    # Background
    pygame.draw.rect(screen, COLORS["health_bar_bg"], (x, y, bar_width, bar_height))

    # Health fill
    ratio = player.health / player.max_health
    fill_w = int(bar_width * ratio)
    if ratio < 0.3:
        color = COLORS["health_bar_damage"]
    elif ratio < 0.6:
        color = (255, 200, 50)
    else:
        color = COLORS["health_bar"]
    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, bar_height))

    # Border
    pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height), 2)

    # Text
    font = pygame.font.Font(None, 18)
    text = font.render(f"{int(player.health)}/{int(player.max_health)}", True, COLORS["text"])
    screen.blit(text, text.get_rect(center=(x + bar_width / 2, y + bar_height / 2)))


def draw_xp_bar(screen, player):
    bar_width = 400
    bar_height = 12
    x = (WINDOW_WIDTH - bar_width) / 2
    y = WINDOW_HEIGHT - 40

    pygame.draw.rect(screen, COLORS["xp_bar_bg"], (x, y, bar_width, bar_height))

    ratio = player.xp / player.xp_to_next
    if ratio > 0:
        fill_w = int(bar_width * ratio)
        pygame.draw.rect(screen, COLORS["xp_bar"], (x, y, fill_w, bar_height))

    pygame.draw.rect(screen, (80, 80, 120), (x, y, bar_width, bar_height), 1)

    font = pygame.font.Font(None, 20)
    text = font.render(f"Lv.{player.level}", True, COLORS["xp_bar"])
    screen.blit(text, text.get_rect(midright=(x - 10, y + bar_height / 2)))


def draw_score(screen, score):
    font = pygame.font.Font(None, 28)
    text = font.render(f"Score: {score}", True, COLORS["text"])
    screen.blit(text, text.get_rect(topright=(WINDOW_WIDTH - 20, 20)))


def draw_wave_announcement(screen, wave, timer):
    if timer <= 0:
        return
    alpha = min(1.0, timer / 2)
    font = pygame.font.Font(None, 60)
    text = font.render(f"Wave {wave}", True, COLORS["wave_text"])
    text.set_alpha(int(255 * alpha))
    rect = text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 3))
    screen.blit(text, rect)


def draw_grid(screen):
    gs = 40
    for x in range(0, WINDOW_WIDTH, gs):
        pygame.draw.line(screen, COLORS["grid"], (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, gs):
        pygame.draw.line(screen, COLORS["grid"], (0, y), (WINDOW_WIDTH, y))


def _wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + " " + w if cur else w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_upgrade_screen(screen, upgrades):
    # Overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Title
    title_font = pygame.font.Font(None, 48)
    text = title_font.render("LEVEL UP!", True, COLORS["xp_bar"])
    screen.blit(text, text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 4)))

    # Cards
    cw, ch = 250, 200
    gap = 30
    total = len(upgrades) * cw + (len(upgrades) - 1) * gap
    start_x = (WINDOW_WIDTH - total) / 2
    card_y = WINDOW_HEIGHT / 2 - ch / 2

    name_font = pygame.font.Font(None, 24)
    desc_font = pygame.font.Font(None, 18)
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for i, upg in enumerate(upgrades):
        cx = start_x + i * (cw + gap)
        rect = pygame.Rect(cx, card_y, cw, ch)
        hovered = rect.collidepoint(mouse_x, mouse_y)

        bg = COLORS["upgrade_hover"] if hovered else COLORS["upgrade_bg"]
        pygame.draw.rect(screen, bg, rect)
        pygame.draw.rect(screen, COLORS["upgrade_border"], rect, 2)

        # Icon circle
        icon_x = cx + cw / 2
        icon_y = card_y + 50
        pygame.draw.circle(screen, upg["color"], (icon_x, icon_y), 30)

        # Name
        name_surf = name_font.render(upg["name"], True, COLORS["text"])
        screen.blit(name_surf, name_surf.get_rect(center=(cx + cw / 2, card_y + 110)))

        # Description
        lines = _wrap_text(upg["description"], desc_font, cw - 20)
        for j, line in enumerate(lines):
            desc_surf = desc_font.render(line, True, COLORS["text_dim"])
            screen.blit(desc_surf, desc_surf.get_rect(center=(cx + cw / 2, card_y + 140 + j * 20)))

        upg["rect"] = rect


def draw_game_over(screen, score, wave):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 72)
    text = title_font.render("GAME OVER", True, COLORS["game_over"])
    screen.blit(text, text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 3)))

    stat_font = pygame.font.Font(None, 32)
    score_surf = stat_font.render(f"Score: {score}", True, COLORS["text"])
    screen.blit(score_surf, score_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 20)))

    wave_surf = stat_font.render(f"Waves Survived: {wave}", True, COLORS["wave_text"])
    screen.blit(wave_surf, wave_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 20)))

    btn_font = pygame.font.Font(None, 36)
    btn = btn_font.render("Click or Press SPACE to Restart", True, COLORS["text"])
    screen.blit(btn, btn.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT * 2 / 3)))
