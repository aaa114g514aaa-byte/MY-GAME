// Space Shooter - A simple C++ game using Win32 API
// 编译: g++ main.cpp -o SpaceShooter.exe -lgdi32 -lwinmm
// 或双击 build.bat

#define WIN32_LEAN_AND_MEAN
#define _USE_MATH_DEFINES
#include <windows.h>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <cstring>

// ─── 游戏常量 ──────────────────────────────────────────
constexpr int WINDOW_W = 640;
constexpr int WINDOW_H = 480;
constexpr int PLAYER_W = 30;
constexpr int PLAYER_H = 20;
constexpr int PLAYER_SPEED = 5;
constexpr int BULLET_W = 4;
constexpr int BULLET_H = 12;
constexpr int BULLET_SPEED = 8;
constexpr int ENEMY_W = 28;
constexpr int ENEMY_H = 20;
constexpr int ENEMY_SPEED = 3;
constexpr int MAX_ENEMIES = 8;
constexpr int ENEMY_SPAWN_DELAY = 45;  // frames
constexpr int PLAYER_MAX_HP = 5;

// ─── 游戏状态 ──────────────────────────────────────────
enum class GameState {
    Playing,
    GameOver
};

struct Player {
    float x, y;
    int hp;
    int invincibleFrames; // 受伤后无敌帧
};

struct Bullet {
    float x, y;
    bool active;
};

struct Enemy {
    float x, y;
    bool active;
    int type;      // 0=普通, 1=快速
    int hp;
};

struct Particle {
    float x, y;
    float vx, vy;
    int life;
    COLORREF color;
};

// ─── 游戏全局变量 ──────────────────────────────────────
Player g_player;
std::vector<Bullet> g_bullets;
std::vector<Enemy> g_enemies;
std::vector<Particle> g_particles;
int g_score = 0;
int g_frameCount = 0;
int g_enemySpawnTimer = 0;
int g_highScore = 0;
GameState g_state = GameState::Playing;
bool g_keys[256] = {false};

// ─── 前向声明 ──────────────────────────────────────────
void spawnParticles(float x, float y, int count, COLORREF color);

// ─── 作弊系统 ──────────────────────────────────────────
std::string g_cheatBuffer;      // 按键序列缓存
int g_cheatTimer = 0;           // 超时重置 (帧数)
bool g_showConsole = false;     // 控制台显示
bool g_godMode = false;         // 无敌模式
bool g_infiniteAmmo = false;    // 无限火力
bool g_showInfo = false;        // 显示状态信息
int g_helpTimer = 0;            // 帮助弹窗剩余帧数

void checkCheatCode(const std::string& input) {
    if (input == "aabbccdd") {
        g_showConsole = !g_showConsole;
        g_cheatBuffer.clear();
    } else if (input == "god") {
        g_godMode = !g_godMode;
        if (g_godMode) g_player.hp = 999;
        g_cheatBuffer.clear();
    } else if (input == "kill") {
        for (auto& e : g_enemies) {
            if (e.active) {
                e.active = false;
                spawnParticles(e.x + ENEMY_W / 2, e.y + ENEMY_H / 2, 10, RGB(255, 100, 50));
                g_score += (e.type == 1) ? 30 : 10;
            }
        }
        g_cheatBuffer.clear();
    } else if (input == "heal") {
        g_player.hp = PLAYER_MAX_HP;
        g_cheatBuffer.clear();
    } else if (input == "boom") {
        g_infiniteAmmo = !g_infiniteAmmo;
        g_cheatBuffer.clear();
    } else if (input == "help") {
        g_helpTimer = 300; // 5秒 (60fps * 5)
        g_cheatBuffer.clear();
    } else if (input == "info") {
        g_showInfo = !g_showInfo;
        g_cheatBuffer.clear();
    }
}

// ─── 工具函数 ──────────────────────────────────────────
int randRange(int min, int max) {
    return min + rand() % (max - min + 1);
}

void spawnParticles(float x, float y, int count, COLORREF color) {
    for (int i = 0; i < count; ++i) {
        float angle = (float)(randRange(0, 360)) * (float)M_PI / 180.0f;
        float speed = (float)(randRange(1, 4));
        g_particles.push_back({
            x, y,
            cosf(angle) * speed,
            sinf(angle) * speed,
            randRange(15, 30),
            color
        });
    }
}

// ─── 初始化 ────────────────────────────────────────────
void initGame() {
    g_player = {
        (float)(WINDOW_W / 2 - PLAYER_W / 2),
        (float)(WINDOW_H - 60),
        PLAYER_MAX_HP,
        0
    };
    g_bullets.clear();
    g_enemies.clear();
    g_particles.clear();
    g_score = 0;
    g_frameCount = 0;
    g_enemySpawnTimer = 0;
    g_state = GameState::Playing;
}

// ─── 碰撞检测 (AABB) ──────────────────────────────────
bool checkCollision(float ax, float ay, float aw, float ah,
                    float bx, float by, float bw, float bh) {
    return (ax < bx + bw && ax + aw > bx &&
            ay < by + bh && ay + ah > by);
}

// ─── 更新逻辑 ──────────────────────────────────────────
void updateGame() {
    if (g_state == GameState::GameOver) {
        if (g_keys[VK_RETURN]) {
            initGame();
        }
        return;
    }

    ++g_frameCount;

    // 作弊输入超时重置
    if (g_cheatTimer > 0) {
        --g_cheatTimer;
        if (g_cheatTimer == 0) g_cheatBuffer.clear();
    }
    if (g_helpTimer > 0) --g_helpTimer;

    // 玩家移动
    float dx = 0, dy = 0;
    if (g_keys[VK_LEFT]  || g_keys['A']) dx -= 1;
    if (g_keys[VK_RIGHT] || g_keys['D']) dx += 1;
    if (g_keys[VK_UP]    || g_keys['W']) dy -= 1;
    if (g_keys[VK_DOWN]  || g_keys['S']) dy += 1;

    if (dx != 0 && dy != 0) {
        dx *= 0.707f; // 对角线归一化
        dy *= 0.707f;
    }

    g_player.x += dx * PLAYER_SPEED;
    g_player.y += dy * PLAYER_SPEED;

    // 边界限制
    g_player.x = std::max(0.0f, std::min((float)(WINDOW_W - PLAYER_W), g_player.x));
    g_player.y = std::max(0.0f, std::min((float)(WINDOW_H - PLAYER_H), g_player.y));

    // 无敌帧递减
    if (g_player.invincibleFrames > 0)
        --g_player.invincibleFrames;

    // 发射子弹 (空格)
    int fireRate = g_infiniteAmmo ? 1 : 4;
    if (g_keys[VK_SPACE] && g_frameCount % fireRate == 0) {
        g_bullets.push_back({
            g_player.x + PLAYER_W / 2 - BULLET_W / 2,
            g_player.y - BULLET_H,
            true
        });
    }

    // 更新子弹
    for (auto& b : g_bullets) {
        if (!b.active) continue;
        b.y -= BULLET_SPEED;
        if (b.y + BULLET_H < 0)
            b.active = false;
    }

    // 生成敌人
    --g_enemySpawnTimer;
    if (g_enemySpawnTimer <= 0 && g_enemies.size() < MAX_ENEMIES) {
        Enemy e;
        e.x = (float)randRange(0, WINDOW_W - ENEMY_W);
        e.y = -ENEMY_H;
        e.active = true;
        e.type = (rand() % 10 < 2) ? 1 : 0; // 20% 快速敌人
        e.hp = (e.type == 1) ? 2 : 1;
        g_enemies.push_back(e);
        g_enemySpawnTimer = std::max(15, ENEMY_SPAWN_DELAY - g_frameCount / 300 * 5);
    }

    // 更新敌人
    for (auto& e : g_enemies) {
        if (!e.active) continue;
        e.y += ENEMY_SPEED + (e.type == 1 ? 2 : 0);
        // 左右摆动
        e.x += sinf((float)(g_frameCount) / 30.0f + e.y / 20.0f) * 0.8f;
        e.x = std::max(0.0f, std::min((float)(WINDOW_W - ENEMY_W), e.x));
        if (e.y > WINDOW_H)
            e.active = false;
    }

    // 子弹 vs 敌人碰撞
    for (auto& b : g_bullets) {
        if (!b.active) continue;
        for (auto& e : g_enemies) {
            if (!e.active) continue;
            if (checkCollision(b.x, b.y, BULLET_W, BULLET_H,
                               e.x, e.y, ENEMY_W, ENEMY_H)) {
                b.active = false;
                --e.hp;
                spawnParticles(e.x + ENEMY_W / 2, e.y + ENEMY_H / 2, 5, RGB(255, 200, 50));
                if (e.hp <= 0) {
                    e.active = false;
                    g_score += (e.type == 1) ? 30 : 10;
                    spawnParticles(e.x + ENEMY_W / 2, e.y + ENEMY_H / 2, 12, RGB(255, 100, 50));
                }
                break;
            }
        }
    }

    // 敌人 vs 玩家碰撞
    if (g_player.invincibleFrames <= 0 && !g_godMode) {
        for (auto& e : g_enemies) {
            if (!e.active) continue;
            if (checkCollision(e.x, e.y, ENEMY_W, ENEMY_H,
                               g_player.x, g_player.y, PLAYER_W, PLAYER_H)) {
                e.active = false;
                --g_player.hp;
                g_player.invincibleFrames = 60; // 1秒无敌
                spawnParticles(g_player.x + PLAYER_W / 2, g_player.y + PLAYER_H / 2, 15, RGB(0, 200, 255));
                if (g_player.hp <= 0) {
                    g_state = GameState::GameOver;
                    if (g_score > g_highScore)
                        g_highScore = g_score;
                    spawnParticles(g_player.x + PLAYER_W / 2, g_player.y + PLAYER_H / 2, 40, RGB(255, 100, 100));
                }
                break;
            }
        }
    }

    // 更新粒子
    for (auto& p : g_particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.1f; // 重力
        --p.life;
    }

    // 清理
    g_bullets.erase(
        std::remove_if(g_bullets.begin(), g_bullets.end(),
            [](const Bullet& b) { return !b.active; }),
        g_bullets.end());

    g_enemies.erase(
        std::remove_if(g_enemies.begin(), g_enemies.end(),
            [](const Enemy& e) { return !e.active; }),
        g_enemies.end());

    g_particles.erase(
        std::remove_if(g_particles.begin(), g_particles.end(),
            [](const Particle& p) { return p.life <= 0; }),
        g_particles.end());
}

// ─── 绘制 ──────────────────────────────────────────────
void drawGame(HDC hdc) {
    // 背景
    HBRUSH bgBrush = CreateSolidBrush(RGB(10, 10, 30));
    RECT rect = {0, 0, WINDOW_W, WINDOW_H};
    FillRect(hdc, &rect, bgBrush);
    DeleteObject(bgBrush);

    // -- 星星背景 --
    static struct Star { int x, y, brightness; } stars[80];
    static bool starsInit = false;
    if (!starsInit) {
        for (int i = 0; i < 80; ++i) {
            stars[i].x = rand() % WINDOW_W;
            stars[i].y = rand() % WINDOW_H;
            stars[i].brightness = rand() % 200 + 55;
        }
        starsInit = true;
    }
    for (const auto& s : stars) {
        SetPixel(hdc, s.x, (s.y + g_frameCount / 2) % WINDOW_H,
                 RGB(s.brightness, s.brightness, s.brightness * 2 / 3));
    }

    // 画笔
    HPEN pen = (HPEN)GetStockObject(NULL_PEN);
    HPEN oldPen = (HPEN)SelectObject(hdc, pen);

    // ── 玩家飞船 ──
    if (g_state == GameState::Playing) {
        // 无敌闪烁
        if (g_player.invincibleFrames > 0 && (g_frameCount / 4) % 2 == 0) {
            // 闪烁时不绘制
        } else {
            HBRUSH playerBrush = CreateSolidBrush(RGB(0, 180, 255));
            SelectObject(hdc, playerBrush);

            // 绘制三角形飞船
            POINT ship[3] = {
                {(int)(g_player.x + PLAYER_W / 2), (int)g_player.y},                           // 顶部(机头)
                {(int)g_player.x,                     (int)(g_player.y + PLAYER_H)},            // 左下
                {(int)(g_player.x + PLAYER_W),         (int)(g_player.y + PLAYER_H)}            // 右下
            };
            Polygon(hdc, ship, 3);

            // 引擎火焰 (根据按键闪烁)
            if (g_keys[VK_UP] || g_keys['W']) {
                HBRUSH flameBrush = CreateSolidBrush(RGB(255, 150, 0));
                SelectObject(hdc, flameBrush);
                POINT flame[3] = {
                    {(int)(g_player.x + PLAYER_W / 2 - 4), (int)(g_player.y + PLAYER_H)},
                    {(int)(g_player.x + PLAYER_W / 2 + 4), (int)(g_player.y + PLAYER_H)},
                    {(int)(g_player.x + PLAYER_W / 2),     (int)(g_player.y + PLAYER_H + 12)}
                };
                Polygon(hdc, flame, 3);
                DeleteObject(flameBrush);
            }

            DeleteObject(playerBrush);

            // 血条
            if (g_godMode) {
                SetTextColor(hdc, RGB(180, 180, 80));
                const char* inf = "HP: INF";
                TextOutA(hdc, WINDOW_W - 60, 10, inf, (int)std::strlen(inf));
            } else {
                for (int i = 0; i < g_player.hp; ++i) {
                    HBRUSH hpBrush = CreateSolidBrush(RGB(255, 50, 50));
                    SelectObject(hdc, hpBrush);
                    RECT hpRect = {WINDOW_W - 30 - i * 22, 10, WINDOW_W - 20 - i * 22, 22};
                    FillRect(hdc, &hpRect, hpBrush);
                    DeleteObject(hpBrush);
                }
            }
        }
    }

    // ── 子弹 ──
    HBRUSH bulletBrush = CreateSolidBrush(RGB(255, 255, 100));
    SelectObject(hdc, bulletBrush);
    for (const auto& b : g_bullets) {
        if (!b.active) continue;
        RECT bRect = {(int)b.x, (int)b.y, (int)(b.x + BULLET_W), (int)(b.y + BULLET_H)};
        FillRect(hdc, &bRect, bulletBrush);
    }
    DeleteObject(bulletBrush);

    // ── 敌人 ──
    for (const auto& e : g_enemies) {
        if (!e.active) continue;
        COLORREF color = (e.type == 1) ? RGB(255, 80, 200) : RGB(255, 60, 60);
        HBRUSH enemyBrush = CreateSolidBrush(color);
        SelectObject(hdc, enemyBrush);

        // 绘制菱形敌人
        POINT diamond[4] = {
            {(int)(e.x + ENEMY_W / 2), (int)e.y},                               // 上
            {(int)(e.x + ENEMY_W),     (int)(e.y + ENEMY_H / 2)},                // 右
            {(int)(e.x + ENEMY_W / 2), (int)(e.y + ENEMY_H)},                    // 下
            {(int)e.x,                 (int)(e.y + ENEMY_H / 2)}                 // 左
        };
        Polygon(hdc, diamond, 4);

        // 眼睛（白点）
        SetPixel(hdc, (int)(e.x + ENEMY_W / 2 - 4), (int)(e.y + ENEMY_H / 2), RGB(255, 255, 255));
        SetPixel(hdc, (int)(e.x + ENEMY_W / 2 + 4), (int)(e.y + ENEMY_H / 2), RGB(255, 255, 255));

        DeleteObject(enemyBrush);
    }

    // ── 粒子 ──
    for (const auto& p : g_particles) {
        int alpha = p.life;
        HBRUSH pBrush = CreateSolidBrush(p.color);
        SelectObject(hdc, pBrush);
        RECT pRect = {(int)p.x - 2, (int)p.y - 2, (int)p.x + 2, (int)p.y + 2};
        FillRect(hdc, &pRect, pBrush);
        DeleteObject(pBrush);
    }

    // ── UI ──
    SetBkMode(hdc, TRANSPARENT);

    // 分数
    std::string scoreText = "SCORE: " + std::to_string(g_score);
    SetTextColor(hdc, RGB(255, 255, 255));
    TextOutA(hdc, 10, 10, scoreText.c_str(), (int)scoreText.length());

    // 最高分
    std::string hsText = "BEST: " + std::to_string(g_highScore);
    SetTextColor(hdc, RGB(150, 150, 150));
    TextOutA(hdc, 10, 28, hsText.c_str(), (int)hsText.length());

    // 帧数 / 敌人数量
    std::string infoText = "ENEMIES: " + std::to_string(g_enemies.size());
    SetTextColor(hdc, RGB(100, 120, 140));
    TextOutA(hdc, 10, 46, infoText.c_str(), (int)infoText.length());

    // ── Game Over ──
    if (g_state == GameState::GameOver) {
        HBRUSH overlay = CreateSolidBrush(RGB(0, 0, 0));
        SelectObject(hdc, overlay);
        RECT fullRect = {0, 0, WINDOW_W, WINDOW_H};
        BLENDFUNCTION bf = {AC_SRC_OVER, 0, 180, 0};
        // 用半透明效果
        FillRect(hdc, &fullRect, overlay);
        DeleteObject(overlay);

        SetTextColor(hdc, RGB(255, 80, 80));
        const char* gameOver = "GAME OVER";
        SetTextAlign(hdc, TA_CENTER);
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 - 40, gameOver, (int)std::strlen(gameOver));

        std::string finalScore = "Score: " + std::to_string(g_score);
        SetTextColor(hdc, RGB(255, 255, 200));
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 + 10, finalScore.c_str(), (int)finalScore.length());

        SetTextColor(hdc, RGB(150, 200, 255));
        const char* restart = "Press ENTER to restart";
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 + 50, restart, (int)std::strlen(restart));
        SetTextAlign(hdc, TA_LEFT);
    }

    // ── 操作提示(初始几秒) ──
    if (g_frameCount < 180 && g_state == GameState::Playing) {
        SetTextColor(hdc, RGB(200, 200, 200));
        SetTextAlign(hdc, TA_CENTER);
        const char* help1 = "ARROW KEYS / WASD - Move";
        const char* help2 = "SPACE - Shoot";
        const char* help3 = "Avoid enemies!";
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 - 20, help1, (int)std::strlen(help1));
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 + 10, help2, (int)std::strlen(help2));
        TextOutA(hdc, WINDOW_W / 2, WINDOW_H / 2 + 40, help3, (int)std::strlen(help3));
        SetTextAlign(hdc, TA_LEFT);
    }

    // ── 帮助弹窗 ──
    if (g_helpTimer > 0) {
        HBRUSH helpBg = CreateSolidBrush(RGB(0, 0, 0));
        RECT helpRect = {WINDOW_W/2 - 170, WINDOW_H/2 - 80, WINDOW_W/2 + 170, WINDOW_H/2 + 80};
        FillRect(hdc, &helpRect, helpBg);
        DeleteObject(helpBg);

        SetTextAlign(hdc, TA_CENTER);
        SetTextColor(hdc, RGB(0, 255, 200));
        const char* title = "=== CHEATS ===";
        TextOutA(hdc, WINDOW_W/2, WINDOW_H/2 - 68, title, (int)std::strlen(title));

        SetTextColor(hdc, RGB(200, 200, 200));
        const char* lines[] = {
            "god     - toggle invincible",
            "kill    - destroy all enemies",
            "heal    - restore HP",
            "boom    - rapid fire toggle",
            "info    - show debug info",
            "aabbccdd - open command input",
        };
        for (int i = 0; i < 6; ++i)
            TextOutA(hdc, WINDOW_W/2, WINDOW_H/2 - 48 + i * 18, lines[i], (int)std::strlen(lines[i]));

        SetTextColor(hdc, RGB(150, 150, 150));
        std::string dismiss = "(auto closes in " + std::to_string(g_helpTimer/60 + 1) + "s)";
        TextOutA(hdc, WINDOW_W/2, WINDOW_H/2 + 64, dismiss.c_str(), (int)dismiss.length());
        SetTextAlign(hdc, TA_LEFT);
    }

    // ── 信息面板 ──
    if (g_showInfo && g_state == GameState::Playing) {
        HBRUSH infoBg = CreateSolidBrush(RGB(0, 0, 0));
        RECT infoRect = {0, 0, WINDOW_W, 70};
        FillRect(hdc, &infoRect, infoBg);
        DeleteObject(infoBg);

        char buf[256];
        SetTextColor(hdc, RGB(0, 255, 100));
        snprintf(buf, sizeof(buf), "GOD:%s  BOOM:%s  HP:%d  SCORE:%d",
                 g_godMode ? "ON" : "OFF", g_infiniteAmmo ? "ON" : "OFF",
                 g_godMode ? 999 : g_player.hp, g_score);
        TextOutA(hdc, 10, 4, buf, (int)std::strlen(buf));

        SetTextColor(hdc, RGB(180, 200, 220));
        snprintf(buf, sizeof(buf), "POS:(%.0f,%.0f)  ENEMIES:%zu  BULLETS:%zu  FRAME:%d",
                 g_player.x, g_player.y, g_enemies.size(), g_bullets.size(), g_frameCount);
        TextOutA(hdc, 10, 22, buf, (int)std::strlen(buf));

        SetTextColor(hdc, RGB(150, 150, 180));
        const char* hint = "type 'help' for cheat list";
        TextOutA(hdc, 10, 40, hint, (int)std::strlen(hint));
    }

    // ── 作弊控制台 ──
    if (g_showConsole) {
        // 半透明背景条
        HBRUSH conBrush = CreateSolidBrush(RGB(0, 0, 0));
        RECT conRect = {0, WINDOW_H - 22, WINDOW_W, WINDOW_H};
        FillRect(hdc, &conRect, conBrush);
        DeleteObject(conBrush);

        // 输入提示
        std::string inputStr = "> " + g_cheatBuffer + ((g_frameCount / 20) % 2 == 0 ? "_" : " ");
        SetTextColor(hdc, RGB(0, 255, 255));
        SetBkMode(hdc, TRANSPARENT);
        TextOutA(hdc, 6, WINDOW_H - 17, inputStr.c_str(), (int)inputStr.length());
    }

    // ── 作弊状态提示 ──
    if (g_godMode && g_state == GameState::Playing) {
        SetTextColor(hdc, RGB(255, 255, 0));
        SetTextAlign(hdc, TA_CENTER);
        const char* godText = "GOD MODE";
        TextOutA(hdc, WINDOW_W / 2, 10, godText, (int)std::strlen(godText));
        SetTextAlign(hdc, TA_LEFT);
    }
    if (g_infiniteAmmo && g_state == GameState::Playing) {
        SetTextColor(hdc, RGB(255, 150, 0));
        SetTextAlign(hdc, TA_CENTER);
        const char* ammoText = "INFINITE AMMO";
        TextOutA(hdc, WINDOW_W / 2, 26, ammoText, (int)std::strlen(ammoText));
        SetTextAlign(hdc, TA_LEFT);
    }

    SelectObject(hdc, oldPen);
}

// ─── Windows 窗口过程 ──────────────────────────────────
LRESULT CALLBACK windowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_KEYDOWN: {
            g_keys[wParam & 0xFF] = true;

            // ── 作弊码输入 ──
            UINT key = wParam;
            if (key >= 'A' && key <= 'Z') {
                char c = (char)(key - 'A' + 'a');
                g_cheatBuffer += c;
                g_cheatTimer = 120; // 2秒内输完
                // 每次追加后都检查所有可能的作弊码
                checkCheatCode(g_cheatBuffer);
            }
            // 退格删除
            if (key == VK_BACK && !g_cheatBuffer.empty()) {
                g_cheatBuffer.pop_back();
                g_cheatTimer = 120;
            }
            // ESC 关闭控制台
            if (key == VK_ESCAPE) {
                g_showConsole = false;
                g_cheatBuffer.clear();
            }
            return 0;
        }

        case WM_KEYUP:
            g_keys[wParam & 0xFF] = false;
            return 0;

        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            HDC memDC = CreateCompatibleDC(hdc);
            HBITMAP memBmp = CreateCompatibleBitmap(hdc, WINDOW_W, WINDOW_H);
            SelectObject(memDC, memBmp);

            drawGame(memDC);

            BitBlt(hdc, 0, 0, WINDOW_W, WINDOW_H, memDC, 0, 0, SRCCOPY);
            DeleteObject(memBmp);
            DeleteDC(memDC);
            EndPaint(hwnd, &ps);
            return 0;
        }

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;

        case WM_ERASEBKGND:
            return 1; // 阻止背景擦除闪烁
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

// ─── 入口 ──────────────────────────────────────────────
int WINAPI WinMain(HINSTANCE hInst, HINSTANCE, LPSTR, int nCmdShow) {
    srand((unsigned int)time(nullptr));

    // 注册窗口类
    const char CLASS_NAME[] = "SpaceShooterWindow";
    WNDCLASSA wc = {};
    wc.lpfnWndProc   = windowProc;
    wc.hInstance     = hInst;
    wc.hCursor       = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)GetStockObject(BLACK_BRUSH);
    wc.lpszClassName = CLASS_NAME;
    RegisterClassA(&wc);

    // 调整窗口大小以适应客户区
    RECT winRect = {0, 0, WINDOW_W, WINDOW_H};
    AdjustWindowRect(&winRect, WS_OVERLAPPEDWINDOW & ~WS_SIZEBOX & ~WS_MAXIMIZEBOX, FALSE);

    HWND hwnd = CreateWindowExA(
        0, CLASS_NAME, "Space Shooter - C++ Game",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT,
        winRect.right - winRect.left,
        winRect.bottom - winRect.top,
        nullptr, nullptr, hInst, nullptr
    );

    if (!hwnd) return 1;

    ShowWindow(hwnd, nCmdShow);

    // 游戏初始化
    initGame();

    // ─── 游戏主循环 ───
    const int TARGET_FPS = 60;
    const int FRAME_DELAY = 1000 / TARGET_FPS;

    MSG msg = {};
    while (msg.message != WM_QUIT) {
        DWORD frameStart = GetTickCount();

        // 处理消息
        while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }

        // 更新游戏逻辑
        updateGame();

        // 重绘窗口
        InvalidateRect(hwnd, nullptr, FALSE);
        UpdateWindow(hwnd);

        // 帧率控制
        DWORD frameTime = GetTickCount() - frameStart;
        if (frameTime < FRAME_DELAY)
            Sleep(FRAME_DELAY - frameTime);

        // 万一GetTickCount溢出的情况, 但不用太在意
    }

    return 0;
}
