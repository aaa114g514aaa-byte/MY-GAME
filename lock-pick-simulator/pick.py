import pygame
import math
import random
import sys
import re
import io

pygame.init()

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

WINDOW_SIZE = 700
LOCK_RADIUS = 155
CONSOLE_HEIGHT = 300
CONSOLE_BG = (30, 30, 35, 230)
CONSOLE_TEXT = (200, 200, 200)

LOCK_OUTER1 = (184, 134, 11)
LOCK_OUTER2 = (218, 165, 32)
LOCK_OUTER3 = (205, 133, 63)
LOCK_OUTER4 = (139, 105, 20)
LOCK_OUTER5 = (101, 67, 33)
LOCK_BORDER = (74, 53, 32)
GOLD = (255, 215, 0)
PICK_COLOR = (136, 153, 170)
RED = (255, 0, 0)

screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("SCUM 开锁模拟器")
clock = pygame.time.Clock()

font = pygame.font.Font('C:\\Windows\\Fonts\\msyh.ttc', 36)
font_small = pygame.font.Font('C:\\Windows\\Fonts\\msyh.ttc', 24)
font_tiny = pygame.font.Font('C:\\Windows\\Fonts\\msyh.ttc', 18)

# 尝试使用等宽字体，如果找不到则使用默认字体
try:
    font_console = pygame.font.Font('C:\\Windows\\Fonts\\msyh.ttc', 16)
except:
    font_console = pygame.font.Font(None, 16)


# LockState 类必须在使用前定义
class LockState:
    def __init__(self):
        self.keyhole_angle = 0
        self.pick_angle = 0
        self.lock_body_rotation = 0
        self.target_rotation = 0
        self.is_success = False
        self.is_success_triggered = False
        self.attempts = 0
        self.is_key_down = False
        self.animation_frame = None
        self.show_success_overlay = False
        self.success_timer = 0
        self.show_info = False

        # 灵敏度相关
        self.mouse_sensitivity = 1.0
        self.prev_mouse_x = None
        self.mouse_relative_mode = True

        # 等待继续
        self.waiting_for_continue = False

        # 锁芯内部旋转
        self.core_rotation = 0


# 全局状态变量
state = LockState()


# 控制台类
class Console:
    def __init__(self):
        self.visible = False
        self.lines = []
        self.max_lines = 50
        self.input_text = ""
        self.history = []
        self.history_index = -1
        self.commands = {
            '/help': self.cmd_help,
            '/clear': self.cmd_clear,
            '/info': self.cmd_info,
            '/set_sensitivity': self.cmd_set_sensitivity,
            '/toggle_mode': self.cmd_toggle_mode,
            '/set_keyhole': self.cmd_set_keyhole,
            '/reset': self.cmd_reset,
            '/quit': self.cmd_quit,
            '/success': self.cmd_success,
        }
        self.log("控制台已启动，输入 /help 查看命令")
        self.log("按 Alt+F12 切换控制台")

    def log(self, message, color=(200, 200, 200)):
        self.lines.append((message, color))
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)

    def cmd_help(self, args):
        self.log("可用命令:", (100, 200, 255))
        self.log("  /help - 显示此帮助", (180, 180, 180))
        self.log("  /clear - 清空控制台", (180, 180, 180))
        self.log("  /info - 显示游戏状态", (180, 180, 180))
        self.log("  /set_sensitivity <value> - 设置灵敏度 (0.1-5.0)", (180, 180, 180))
        self.log("  /toggle_mode - 切换鼠标模式", (180, 180, 180))
        self.log("  /set_keyhole <angle> - 设置钥匙孔角度 (0-240)", (180, 180, 180))
        self.log("  /reset - 重置锁", (180, 180, 180))
        self.log("  /success - 强制开锁成功", (180, 180, 180))
        self.log("  /quit - 退出游戏", (180, 180, 180))

    def cmd_clear(self, args):
        self.lines.clear()
        self.log("控制台已清空")

    def cmd_info(self, args=None):
        state.show_info = not state.show_info  # 切换显示状态
        if state.show_info:
            self.log("实时信息已开启", (0, 255, 0))
            self.log("=== 游戏状态 ===", (100, 200, 255))
            self.log(f"  尝试次数: {state.attempts}", (180, 180, 180))
            self.log(f"  钥匙孔角度: {state.keyhole_angle:.2f}°", (180, 180, 180))
            self.log(f"  开锁器角度: {state.pick_angle:.2f}°", (180, 180, 180))
            self.log(f"  锁体旋转: {state.lock_body_rotation:.2f}°", (180, 180, 180))
            self.log(f"  目标旋转: {state.target_rotation:.2f}°", (180, 180, 180))
            self.log(f"  距离: {abs(state.pick_angle - state.keyhole_angle):.2f}°", (180, 180, 180))
            self.log(f"  是否成功: {state.is_success}", (180, 180, 180))
            self.log(f"  灵敏度: {state.mouse_sensitivity:.1f}x", (180, 180, 180))
            self.log(f"  鼠标模式: {'相对' if state.mouse_relative_mode else '绝对'}", (180, 180, 180))
            self.log(f"  是否按F: {state.is_key_down}", (180, 180, 180))
            if state.is_success:
                self.log("  状态: 已开锁！按空格继续", (0, 255, 0))
            else:
                self.log("  状态: 锁定中", (255, 100, 100))
        else:
            self.log("实时信息已关闭", (255, 200, 100))

    def cmd_set_sensitivity(self, args):
        if len(args) < 1:
            self.log("用法: /set_sensitivity <值> (0.1-5.0)", (255, 200, 100))
            return
        try:
            val = float(args[0])
            if 0.1 <= val <= 5.0:
                state.mouse_sensitivity = val
                self.log(f"灵敏度已设置为 {val:.1f}x", (0, 255, 0))
            else:
                self.log("灵敏度必须在 0.1 到 5.0 之间", (255, 100, 100))
        except ValueError:
            self.log("请输入有效数字", (255, 100, 100))

    def cmd_toggle_mode(self, args):
        state.mouse_relative_mode = not state.mouse_relative_mode
        state.prev_mouse_x = None
        mode = "相对" if state.mouse_relative_mode else "绝对"
        self.log(f"已切换到 {mode} 模式", (0, 255, 0))

    def cmd_set_keyhole(self, args):
        if len(args) < 1:
            self.log("用法: /set_keyhole <角度> (0-240)", (255, 200, 100))
            return
        try:
            val = float(args[0])
            if 0 <= val <= 240:
                state.keyhole_angle = val
                self.log(f"钥匙孔角度已设置为 {val:.1f}°", (0, 255, 0))
            else:
                self.log("角度必须在 0 到 240 之间", (255, 100, 100))
        except ValueError:
            self.log("请输入有效数字", (255, 100, 100))

    def cmd_reset(self, args):
        init_lock()
        self.log("锁已重置", (0, 255, 0))

    def cmd_success(self, args):
        if not state.is_success:
            state.is_success = True
            state.is_success_triggered = False
            state.target_rotation = 90
            state.attempts += 1
            start_spring()
            self.log("强制开锁成功！", (0, 255, 0))
        else:
            self.log("已经开锁成功了", (255, 200, 100))

    def cmd_quit(self, args):
        self.log("正在退出游戏...", (255, 200, 100))
        pygame.quit()
        sys.exit()

    def execute_command(self, cmd):
        parts = cmd.strip().split()
        if not parts:
            return
        command = parts[0].lower()
        args = parts[1:]

        if command in self.commands:
            self.commands[command](args)
        else:
            self.log(f"未知命令: {command}，输入 /help 查看可用命令", (255, 100, 100))

    def handle_keydown(self, event):
        if event.key == pygame.K_RETURN:
            if self.input_text:
                self.log(f"> {self.input_text}", (100, 255, 100))
                self.history.append(self.input_text)
                self.history_index = len(self.history)
                self.execute_command(self.input_text)
                self.input_text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_UP:
            if self.history_index > 0:
                self.history_index -= 1
                self.input_text = self.history[self.history_index]
        elif event.key == pygame.K_DOWN:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.input_text = self.history[self.history_index]
            else:
                self.history_index = len(self.history)
                self.input_text = ""
        elif event.key == pygame.K_ESCAPE:
            self.visible = False
        else:
            # 输入字符
            if event.unicode and event.unicode.isprintable():
                self.input_text += event.unicode

    def draw(self):
        if not self.visible:
            return

        console_surface = pygame.Surface((WINDOW_SIZE, CONSOLE_HEIGHT), pygame.SRCALPHA)
        console_surface.fill(CONSOLE_BG)

        # 绘制边框
        pygame.draw.rect(console_surface, (80, 80, 80),
                         (0, 0, WINDOW_SIZE, CONSOLE_HEIGHT), 2)

        # 绘制标题栏
        title_surface = font_tiny.render("=== 控制台 ===", True, (100, 200, 255))
        console_surface.blit(title_surface, (10, 5))

        # 绘制日志
        y_offset = 35
        line_height = 20
        visible_lines = self.lines[-int((CONSOLE_HEIGHT - 60) / line_height):]
        for line, color in visible_lines:
            # 如果文字太长，进行截断
            if len(line) > 60:
                line = line[:57] + "..."
            text_surface = font_console.render(line, True, color)
            console_surface.blit(text_surface, (10, y_offset))
            y_offset += line_height

        # 绘制输入框
        input_y = CONSOLE_HEIGHT - 30
        # 输入框背景
        pygame.draw.rect(console_surface, (50, 50, 55),
                         (5, input_y - 2, WINDOW_SIZE - 10, 26))
        pygame.draw.rect(console_surface, (80, 80, 80),
                         (5, input_y - 2, WINDOW_SIZE - 10, 26), 1)

        # 输入提示和文字
        prompt = font_console.render("> ", True, (100, 255, 100))
        console_surface.blit(prompt, (10, input_y))

        # 如果输入框激活，显示闪烁光标
        display_text = self.input_text
        if pygame.time.get_ticks() % 1000 < 500:
            display_text += "▌"
        text_surface = font_console.render(display_text, True, (255, 255, 255))
        console_surface.blit(text_surface, (30, input_y))

        screen.blit(console_surface, (0, WINDOW_SIZE - CONSOLE_HEIGHT))


# 全局控制台实例
console = Console()


def init_lock():
    state.keyhole_angle = random.random() * 240
    state.pick_angle = 0
    state.lock_body_rotation = 0
    state.target_rotation = 0
    state.is_success = False
    state.is_success_triggered = False
    state.attempts = 0
    state.is_key_down = False
    state.show_success_overlay = False
    state.success_timer = 0
    state.prev_mouse_x = None
    state.waiting_for_continue = False
    state.animation_frame = None
    state.core_rotation = 0
    console.log("锁已重置", (0, 255, 0))


def deg_to_rad(deg):
    return deg * math.pi / 180


def internal_to_abs(internal_deg):
    if internal_deg < 120:
        return internal_deg + 240
    return internal_deg - 120


def to_canvas_rad(abs_deg):
    return deg_to_rad(abs_deg - 90)


def get_distance(internal_angle):
    return abs(internal_angle - state.keyhole_angle)


def compute_target_rotation(internal_angle):
    if state.is_success:
        return 90
    dist = get_distance(internal_angle)
    if dist >= 30:
        return 0
    t = 1 - (dist / 30)
    return t * 85


def spring_animation():
    diff = state.target_rotation - state.lock_body_rotation
    if abs(diff) < 0.1:
        state.lock_body_rotation = state.target_rotation
        state.core_rotation = state.lock_body_rotation

        if state.is_success and state.lock_body_rotation >= 89.5 and not state.is_success_triggered:
            state.is_success_triggered = True
            state.show_success_overlay = True
            state.waiting_for_continue = True
            console.log("🎉 开锁成功！", (0, 255, 0))
        state.animation_frame = None
        return
    state.lock_body_rotation += diff * 0.08
    state.core_rotation += diff * 0.07
    state.animation_frame = True


def start_spring():
    state.animation_frame = True


def update_spring():
    if state.animation_frame:
        spring_animation()


def on_key_down():
    if state.is_success:
        return
    if state.is_key_down:
        return
    state.is_key_down = True
    dist = get_distance(state.pick_angle)
    console.log(f"按F - 距离: {dist:.2f}°", (200, 200, 200))
    if dist <= 3:
        state.is_success = True
        state.is_success_triggered = False
        state.target_rotation = 90
        state.attempts += 1
        start_spring()
        console.log("✅ 开锁成功！", (0, 255, 0))
        return
    if dist <= 30:
        state.target_rotation = compute_target_rotation(state.pick_angle)
        start_spring()
        console.log(f"📐 部分转动: {state.target_rotation:.1f}°", (255, 200, 100))
    else:
        state.target_rotation = 5
        start_spring()
        console.log("❌ 距离太远", (255, 100, 100))


def on_key_up():
    if state.is_success:
        state.is_key_down = False
        return
    state.is_key_down = False
    state.target_rotation = 0
    start_spring()
    console.log("松开F - 弹回", (200, 200, 200))


def draw_background():
    screen.fill((10, 10, 15))


def draw_lock_body(rotation):
    cx, cy = WINDOW_SIZE // 2, WINDOW_SIZE // 2

    pygame.draw.circle(screen, LOCK_OUTER5, (cx, cy), LOCK_RADIUS + 6)
    pygame.draw.circle(screen, LOCK_OUTER4, (cx, cy), LOCK_RADIUS + 4)
    pygame.draw.circle(screen, LOCK_OUTER3, (cx, cy), LOCK_RADIUS)
    pygame.draw.circle(screen, LOCK_OUTER2, (cx, cy), LOCK_RADIUS - 2)
    pygame.draw.circle(screen, LOCK_OUTER1, (cx, cy), LOCK_RADIUS - 4)
    pygame.draw.circle(screen, LOCK_BORDER, (cx, cy), LOCK_RADIUS + 2, 12)

    for i in range(8):
        angle = (i / 8) * 2 * math.pi
        r = LOCK_RADIUS - 18
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pygame.draw.circle(screen, (180, 140, 80), (int(x), int(y)), 4)
        pygame.draw.circle(screen, (100, 70, 30), (int(x), int(y)), 4, 1)

    core_radius = 85
    core_surface = pygame.Surface((core_radius * 2 + 10, core_radius * 2 + 10), pygame.SRCALPHA)
    core_center = (core_radius + 5, core_radius + 5)

    for i in range(3):
        r = core_radius - i * 2
        color = (58 + i * 8, 58 + i * 8, 66 + i * 8)
        pygame.draw.circle(core_surface, color, core_center, r)
    pygame.draw.circle(core_surface, (200, 169, 110, 38), core_center, core_radius, 2)
    pygame.draw.circle(core_surface, (200, 169, 110, 20), core_center, core_radius - 20, 1)

    for i in range(6):
        angle = (i / 6) * 2 * math.pi + deg_to_rad(rotation)
        r1 = core_radius - 10
        r2 = core_radius - 30
        x1 = core_center[0] + r1 * math.cos(angle)
        y1 = core_center[1] + r1 * math.sin(angle)
        x2 = core_center[0] + r2 * math.cos(angle)
        y2 = core_center[1] + r2 * math.sin(angle)
        pygame.draw.line(core_surface, (80, 80, 90), (x1, y1), (x2, y2), 1)

    rotated_core = pygame.transform.rotate(core_surface, rotation)
    rect = rotated_core.get_rect(center=(cx, cy))
    screen.blit(rotated_core, rect)


def draw_keyhole(rotation):
    cx, cy = WINDOW_SIZE // 2, WINDOW_SIZE // 2
    keyhole_w, keyhole_h = 20, 60
    half_w = keyhole_w // 2
    half_h = keyhole_h // 2
    angle_rad = deg_to_rad(rotation)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
    points = []
    for dx, dy in corners:
        rx = cx + dx * cos_a - dy * sin_a
        ry = cy + dx * sin_a + dy * cos_a
        points.append((rx, ry))
    pygame.draw.lines(screen, (138, 122, 90), True, points, 2)


def draw_pick_indicator():
    if state.pick_angle is None:
        return
    cx, cy = WINDOW_SIZE // 2, WINDOW_SIZE // 2
    abs_angle = internal_to_abs(state.pick_angle)
    rad = to_canvas_rad(abs_angle)

    color = RED

    start_x = cx + 85 * math.cos(rad)
    start_y = cy + 85 * math.sin(rad)
    end_x = cx + 185 * math.cos(rad)
    end_y = cy + 185 * math.sin(rad)

    pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 6)
    pygame.draw.circle(screen, color, (int(end_x), int(end_y)), 8)


def draw_ui():
    text = font.render(f"尝试: {state.attempts}", True, (200, 169, 110))
    screen.blit(text, (20, 20))
    title = font.render("SCUM 开锁模拟器", True, (200, 169, 110))
    title_rect = title.get_rect(center=(WINDOW_SIZE // 2, 25))
    screen.blit(title, title_rect)

    sens_text = font_tiny.render(f"灵敏度: {state.mouse_sensitivity:.1f}x  [↑↓调整]", True, (150, 150, 150))
    screen.blit(sens_text, (20, 70))

    mode_text = font_tiny.render(f"模式: {'相对' if state.mouse_relative_mode else '绝对'} [M切换]", True,
                                 (150, 150, 150))
    screen.blit(mode_text, (20, 95))

    # 显示控制台快捷键提示
    console_hint = font_tiny.render("[Alt+F12 控制台]", True, (80, 80, 80))
    screen.blit(console_hint, (WINDOW_SIZE - 150, 20))

    if not state.is_success:
        hint = font_small.render("移动鼠标旋转开锁器 · 按住F转动锁体 · 松开弹回", True, (85, 85, 85))
        hint_rect = hint.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE - 30))
        screen.blit(hint, hint_rect)
    elif state.waiting_for_continue:
        continue_text = font.render("按 空格键 继续", True, GOLD)
        continue_rect = continue_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 60))
        alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() / 500))
        continue_text.set_alpha(alpha)
        screen.blit(continue_text, continue_rect)

    if state.show_info:
        info_y = 130
        info_lines = [
            f"钥匙孔: {state.keyhole_angle:.1f}°",
            f"开锁器: {state.pick_angle:.1f}°",
            f"距离: {abs(state.pick_angle - state.keyhole_angle):.1f}°",
            f"锁体旋转: {state.lock_body_rotation:.1f}°",
            f"目标旋转: {state.target_rotation:.1f}°",
            f"状态: {'✅ 已开锁' if state.is_success else '🔒 锁定中'}",
            f"灵敏度: {state.mouse_sensitivity:.1f}x",
            f"模式: {'相对' if state.mouse_relative_mode else '绝对'}"
        ]
        for line in info_lines:
            text = font_tiny.render(line, True, (100, 200, 255))
            screen.blit(text, (20, info_y))
            info_y += 22


def draw_success_overlay():
    if not state.show_success_overlay:
        return
    bar_height = 80
    bar_y = WINDOW_SIZE // 2 - bar_height // 2
    bar = pygame.Surface((WINDOW_SIZE, bar_height), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 150))
    screen.blit(bar, (0, bar_y))
    title = font.render("开锁成功!", True, GOLD)
    title_rect = title.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 10))
    screen.blit(title, title_rect)


def main():
    init_lock()
    running = True

    SENSITIVITY_STEP = 0.1
    MIN_SENSITIVITY = 0.1
    MAX_SENSITIVITY = 5.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # 处理控制台快捷键 (Alt+F12)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12 and (event.mod & pygame.KMOD_ALT):
                    console.visible = not console.visible
                    if console.visible:
                        console.log("控制台已打开", (0, 255, 0))
                    continue

            # 如果控制台可见，优先处理控制台输入
            if console.visible:
                if event.type == pygame.KEYDOWN:
                    console.handle_keydown(event)
                continue  # 控制台打开时阻止其他输入

            # 正常游戏输入
            if event.type == pygame.MOUSEMOTION:
                if state.is_success or state.waiting_for_continue:
                    continue

                if state.mouse_relative_mode:
                    if state.prev_mouse_x is None:
                        state.prev_mouse_x = event.pos[0]

                    dx = event.pos[0] - state.prev_mouse_x
                    state.pick_angle += dx * state.mouse_sensitivity * 0.3
                    state.prev_mouse_x = event.pos[0]
                else:
                    state.pick_angle = (event.pos[0] / WINDOW_SIZE) * 240

                state.pick_angle = max(0, min(240, state.pick_angle))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and state.waiting_for_continue:
                    init_lock()
                    continue

                if event.key == pygame.K_f and not state.is_key_down and not state.is_success:
                    on_key_down()
                elif event.key == pygame.K_UP:
                    state.mouse_sensitivity = min(MAX_SENSITIVITY,
                                                  state.mouse_sensitivity + SENSITIVITY_STEP)
                elif event.key == pygame.K_DOWN:
                    state.mouse_sensitivity = max(MIN_SENSITIVITY,
                                                  state.mouse_sensitivity - SENSITIVITY_STEP)
                elif event.key == pygame.K_m:
                    state.mouse_relative_mode = not state.mouse_relative_mode
                    state.prev_mouse_x = None

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_f and state.is_key_down:
                    on_key_up()

        update_spring()

        draw_background()
        draw_lock_body(state.lock_body_rotation)
        draw_pick_indicator()
        draw_keyhole(state.lock_body_rotation)
        draw_ui()

        if state.show_success_overlay:
            draw_success_overlay()

        # 绘制控制台（在最上层）
        console.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()