"""
Zippo 打火机 — 点击滚轮开盖点火，按住燃烧，松手熄火
"""

import pygame, sys, math, random, array

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)
W, H = 520, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Zippo 打火机")
clock = pygame.time.Clock()

# 字体
font = font_s = None
try:
    font = pygame.font.SysFont("simhei", 24)
    font_s = pygame.font.SysFont("simhei", 18)
except:
    pass
if font is None:
    try:
        font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 24)
        font_s = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 18)
    except:
        font = pygame.font.Font(None, 28)
        font_s = pygame.font.Font(None, 22)
        _EN = True
    else:
        _EN = False
else:
    _EN = False

# 颜色
CR = (192, 196, 202)
CD = (128, 132, 138)
CL = (224, 228, 234)
ST = (100, 104, 108)
B1 = (68, 24, 20)
B2 = (46, 12, 10)
IN = (56, 52, 48)    # 盖子内侧颜色（翻开后可见）
BK = (10, 10, 10)
WT = (255, 255, 255)
GN = (50, 200, 50)
YW = (255, 220, 60)
RD = (255, 50, 10)
BG = (34, 30, 28)
WK = (65, 62, 55)

# 火焰颜色
F_OUT = [(255, max(0, 180 - i * 25), max(0, 70 - i * 16)) for i in range(8)]
F_INN = [(min(255, 60 + i * 25), min(255, 130 + i * 15), 255) for i in range(5)]

# ---- 音效 ----
def _mk_buf(dur, vol, freqs=None, noise=False, decay=3):
    """生成音频 buffer，decay 控制衰减速度（指数衰减系数）"""
    sr = 22050
    n = int(sr * dur)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        env = math.exp(-t * decay)
        val = 0
        if noise:
            val += random.uniform(-1, 1) * 1.0
        if freqs:
            for f in freqs:
                val += math.sin(2 * math.pi * f * t) * 0.5
        val = int(32767 * env * vol * val)
        buf[i] = max(-32767, min(32767, val))
    return buf

def _mk_snd(*bufs):
    """合并多个 buffer 为一个 Sound"""
    max_len = max(len(b) for b in bufs)
    merged = array.array('h', [0]) * max_len
    for b in bufs:
        for i in range(len(b)):
            merged[i] = max(-32767, min(32767, merged[i] + b[i]))
    return pygame.mixer.Sound(buffer=merged)

b_open = _mk_buf(0.40, 0.07, freqs=[1760, 2640], decay=4)
b_close = _mk_buf(0.06, 0.12, freqs=[1400, 800])
b_tick = _mk_buf(0.035, 0.20, noise=True)
b_flame_n = _mk_buf(0.18, 0.10, noise=True)
b_flame_t = _mk_buf(0.12, 0.06, freqs=[130, 260])

snd_open = pygame.mixer.Sound(buffer=b_open)
snd_close = pygame.mixer.Sound(buffer=b_close)
snd_tick = pygame.mixer.Sound(buffer=b_tick)
snd_flame = _mk_snd(b_flame_n, b_flame_t)

# ---- Zippo 尺寸 ----
ZW, ZH = 160, 240       # 宽高
LH = 66                 # 盖子高度（加大，遮住滚轮）
BH = ZH - LH            # 机身高度
zx = W // 2 - ZW // 2
zy = H // 2 - ZH // 2 + 30

# 铰链位置（在机身顶部，盖子与机身交界处）
hx = zx                # 铰链 X
hy = zy + LH           # 铰链 Y

# 滚轮位置（加大）— 在火焰右侧，完全被盖子遮挡
wx = zx + ZW // 2 + 50
wy = zy + LH - 22
wr = 20                # 滚轮加大

# 防风罩 — 和滚轮一起在右侧
cx = zx + ZW // 2 - 10
WH = 48                 # 防风罩铁片高度
cy = zy + LH - WH       # 火焰底部 Y

# ---- 状态 ----
flame = False
open_lid = False
lid_t = 0.0
sparks = []
pts = []
hover = False

class Spk:
    def __init__(self, x, y):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        a = random.uniform(0, 6.28)
        s = random.uniform(2, 6)
        self.vx = math.cos(a) * s
        self.vy = math.sin(a) * s
        self.lf = random.uniform(0.12, 0.4)
        self.age = 0
    def up(self, dt):
        self.age += dt
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 1.5 * dt * 60
    def a(self):
        return max(0, 1 - self.age / self.lf)
    def live(self):
        return self.age < self.lf

class Ptc:
    def __init__(self, x, y):
        self.x = x + random.uniform(-3, 3)
        self.y = y
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-2.5, -0.8)
        self.sz = random.uniform(3, 6)
        self.lf = random.uniform(0.2, 0.5)
        self.age = 0
    def up(self, dt):
        self.age += dt
        self.vx += random.uniform(-0.2, 0.2)
        self.vy += random.uniform(-0.1, 0.1)
        self.x += self.vx
        self.y += self.vy
        self.sz *= 0.96
    def a(self):
        return max(0, 1 - self.age / self.lf)
    def live(self):
        return self.age < self.lf and self.sz > 0.5

# ========== 绘制 ==========

def draw_zippo():
    """
    正面视角 Zippo，盖子向上翻（铰链在机身顶部背面）
    0°→90°：盖子从全高压缩成一条线（前表面）
    90°→170°：盖子从一条线展开为全高（内侧面朝前）
    """
    global lid_t
    target = 1.0 if open_lid else 0.0
    lid_t += (target - lid_t) * 0.10
    if abs(lid_t - target) < 0.0005:
        lid_t = target
    lt = lid_t

    # ---- 机身 ----
    body = pygame.Rect(zx, zy + LH, ZW, BH)
    pygame.draw.rect(screen, CR, body, border_radius=5)
    bot = pygame.Rect(zx, zy + LH + BH - 14, ZW, 14)
    pygame.draw.rect(screen, B1, bot, border_radius=5)
    pygame.draw.rect(screen, CL, body, width=2, border_radius=5)

    # ZIPPO 标志
    lo = font_s.render("ZIPPO", True, CD)
    screen.blit(lo, (zx + ZW // 2 - lo.get_width() // 2, zy + LH + BH // 2 - 6))
    pygame.draw.line(screen, CD, (zx + 28, zy + LH + BH // 2 + 14),
                     (zx + ZW - 28, zy + LH + BH // 2 + 14), 1)

    # ---- 铰链（在机身顶部的连接处）----
    for i in range(5):
        hxi = hx + 8 + i * (ZW - 16) // 4
        pygame.draw.circle(screen, CD, (hxi, hy), 4)
        pygame.draw.circle(screen, CL, (hxi - 1, hy - 1), 2)

    # ---- 滚轮（一直显示，跨在盖子/机身交界处）----
    pygame.draw.circle(screen, (100, 100, 100), (wx, wy), wr)
    pygame.draw.circle(screen, (150, 150, 150), (wx, wy), wr, 2)
    for i in range(14):
        a = math.radians(i * 25.7)
        r1, r2 = wr - 7, wr - 1
        pygame.draw.line(screen, (80, 80, 80),
            (wx + math.cos(a) * r1, wy + math.sin(a) * r1),
            (wx + math.cos(a) * r2, wy + math.sin(a) * r2), 2)
    pygame.draw.circle(screen, CD, (wx, wy), 6)
    pygame.draw.circle(screen, CL, (wx, wy), 4)

    if hover:
        hl = pygame.Surface((wr * 2 + 6, wr * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(hl, (255, 255, 200, 25), (wr + 3, wr + 3), wr + 1)
        screen.blit(hl, (wx - wr - 3, wy - wr - 3))

    # ---- 防风罩（铁片+9孔+棉芯，盖子在上层遮挡）----
    ws_w, ws_h = 56, WH
    ws_x = cx - ws_w // 2
    ws_y = zy + LH - ws_h
    hole_r = 5
    gap = 18

    pygame.draw.rect(screen, ST, (ws_x, ws_y, ws_w, ws_h), border_radius=3)
    pygame.draw.rect(screen, CD, (ws_x, ws_y, ws_w, ws_h), width=2, border_radius=3)

    wick_w = 12
    pygame.draw.rect(screen, WT, (cx - wick_w // 2, ws_y + 5, wick_w, ws_h - 10))

    cx_center = ws_x + ws_w // 2
    cy_center = ws_y + ws_h // 2
    for row in range(3):
        for col in range(3):
            hx_hole = cx_center - gap + col * gap
            hy_hole = cy_center - gap + row * gap
            pygame.draw.circle(screen, BK, (hx_hole, hy_hole), hole_r)
            pygame.draw.circle(screen, (80, 80, 85), (hx_hole, hy_hole), hole_r, 1)

    # ---- 盖子（向左做圆周运动）----
    # 铰链在盖子左下角 (zx+2, zy+LH)
    # 盖子绕铰链向左旋转 0°→145°
    if lt < 0.01:
        # 完全闭合
        lr = pygame.Rect(zx + 2, zy, ZW - 4, LH)
        pygame.draw.rect(screen, CR, lr, border_radius=5)
        pygame.draw.rect(screen, CL, lr, width=2, border_radius=5)
        pygame.draw.arc(screen, CL, (zx + 2, zy - 2, ZW - 4, 10), math.pi, 0, 2)

    else:
        # 创建盖子表面
        lid_surf = pygame.Surface((ZW - 4, LH), pygame.SRCALPHA)
        angle = lt * 145  # 当前角度 0°→145°

        # 单一颜色，不模拟内部
        pygame.draw.rect(lid_surf, CR, lid_surf.get_rect(), border_radius=5)
        pygame.draw.rect(lid_surf, CL, lid_surf.get_rect(), width=2, border_radius=5)

        # 绕左下角铰链 (zx+2, zy+LH) 向左旋转
        hinge_screen = (zx + 2, zy + LH)
        hinge_local = (0, LH)

        image_rect = lid_surf.get_rect(
            topleft=(hinge_screen[0] - hinge_local[0],
                     hinge_screen[1] - hinge_local[1]))
        offset = pygame.math.Vector2(hinge_screen) - image_rect.center
        rotated_offset = offset.rotate(-angle)
        center = hinge_screen - rotated_offset
        rotated_image = pygame.transform.rotate(lid_surf, angle)
        screen.blit(rotated_image, rotated_image.get_rect(center=center))

def draw_flame():
    """加宽火焰"""
    if not open_lid or not flame:
        return
    flick = random.uniform(0.9, 1.1)
    drift = random.uniform(-3, 3)
    bx, by = cx, cy + 2

    fh = 60 * flick
    fw = 24  # 加宽

    # 外层火焰
    for i in range(10):
        t = i / 10
        h = fh * t
        w = fw * (1 - t * 0.55) * max(0.1, 1 - abs(t - 0.5) * 1.8)
        if w < 2.5:
            continue
        wy = by - h + random.uniform(-0.5, 0.5)
        wx = bx + drift * t
        ci = min(7, i)
        c = F_OUT[ci]
        pygame.draw.ellipse(screen, c, (wx - w / 2, wy - 3, w, 6 + t * 4))

    # 内焰（蓝色）
    ih = fh * 0.4
    for i in range(5):
        t = i / 5
        h = ih * t
        w = 10 * (1 - t * 0.3)
        if w < 1.5:
            continue
        wy = by - h + random.uniform(-0.5, 0.5)
        wx = bx + drift * t * 0.3
        ci = min(4, i)
        c = F_INN[ci]
        pygame.draw.ellipse(screen, c, (wx - w / 2, wy - 1, w, 4 + t * 2))

    # 焰心
    pygame.draw.circle(screen, (255, 250, 230), (bx + drift * 0.1, by - 1), 6)
    pygame.draw.circle(screen, (255, 255, 255), (bx + drift * 0.1, by - 1), 3)

    # 粒子
    for p in pts:
        if p.live():
            a = p.a()
            idx = min(7, max(0, int(p.sz)))
            base = F_OUT[idx] if p.sz > 4 else F_INN[min(4, int(p.sz))]
            c = tuple(min(255, int(v * a)) for v in base)
            sz = max(1, int(p.sz * a))
            pygame.draw.circle(screen, c, (int(p.x), int(p.y)), sz)


def draw_sparks():
    for s in sparks:
        if s.live():
            a = s.a()
            pygame.draw.circle(screen, (255, int(200 * a), int(50 * a)),
                               (int(s.x), int(s.y)), max(1, int(3 * a)))
            pygame.draw.circle(screen, (255, 255, 200),
                               (int(s.x), int(s.y)), max(1, int(1.5 * a)))


def draw_ui():
    if not open_lid:
        tip = "空格开盖 · 滚轮打火" if not _EN else "SPACE to open · Click to spark"
    elif flame:
        tip = "燃烧中 · 空格关盖灭火" if not _EN else "Burning · SPACE to close"
    else:
        tip = "点击滚轮点火" if not _EN else "Click wheel to ignite"
    t = font_s.render(tip, True, (160, 155, 150))
    screen.blit(t, (W // 2 - t.get_width() // 2, H - 50))


def on_wheel(mx, my):
    return (mx - wx) ** 2 + (my - wy) ** 2 <= (wr + 14) ** 2


# ===== 主循环 =====
running = True
dt = 0

while running:
    dt = clock.tick(60) / 1000.0
    dt = min(dt, 0.05)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            open_lid = not open_lid
            if open_lid:
                snd_open.play()
            else:
                snd_close.play()
                flame = False

    mx, my = pygame.mouse.get_pos()
    btns = pygame.mouse.get_pressed()
    hover = on_wheel(mx, my)

    if btns[0] and hover and open_lid and not flame:
        flame = True
        snd_tick.play()
        snd_flame.play()
        for _ in range(12):
            sparks.append(Spk(cx, cy))

    for s in sparks[:]:
        s.up(dt)
        if not s.live():
            sparks.remove(s)

    if flame:
        for _ in range(3):
            pts.append(Ptc(cx, cy))
    for p in pts[:]:
        p.up(dt)
        if not p.live():
            pts.remove(p)
    while len(pts) > 50:
        pts.pop(0)

    screen.fill(BG)
    draw_ui()
    draw_zippo()
    draw_sparks()
    draw_flame()
    pygame.display.flip()

pygame.quit()
sys.exit()
