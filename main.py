import pygame
import random
import sys

# Инициализация
pygame.init()

# Подстраиваемся под разрешение экрана телефона
info = pygame.display.Info()
WIDTH = info.current_w if info.current_w > 0 else 450
HEIGHT = info.current_h if info.current_h > 0 else 800

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Цвета (Неоновая палитра)
BG_COLOR = (10, 10, 22)
PLAYER_COLOR = (0, 255, 255)       # Циан
ENEMY_COLOR = (255, 0, 128)        # Пурпурный
BULLET_COLOR = (255, 255, 0)       # Желтый
STAR_COLOR = (100, 100, 150)
HEALTH_COLOR = (0, 255, 100)       # Зеленый для здоровья
POW_DOUBLE_COLOR = (255, 128, 0)   # Оранжевый для двойного выстрела

# Игровые параметры корабля
player_size = int(WIDTH * 0.08)
player_x = WIDTH // 2
player_y = int(HEIGHT * 0.85)
player_speed = 0.2 

# Здоровье
MAX_HEALTH = 5
health = MAX_HEALTH

# Модификаторы стрельбы
double_shot = False
double_shot_timer = 0

bullets = []
bullet_speed = int(HEIGHT * 0.02)
reload_time = 12
reload_counter = 0

enemies = []
enemy_speed_min = int(HEIGHT * 0.005)
enemy_speed_max = int(HEIGHT * 0.012)
spawn_rate = 30
spawn_counter = 0

# Сферы улучшений
powerups = []
powerup_speed = int(HEIGHT * 0.006)

particles = []  
stars = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), "speed": random.uniform(1, 4)} for _ in range(50)]

score = 0
game_over = False

def create_explosion(x, y, color):
    """Эффект сочного неонового взрыва"""
    for _ in range(15):
        particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-5, 5),
            "vy": random.uniform(-5, 5),
            "radius": random.randint(3, 6),
            "color": color,
            "life": 1.0
        })

# Главный цикл
running = True
while running:
    screen.fill(BG_COLOR)
    
    # События
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and game_over:
            # Сброс всех параметров при перезапуске
            game_over = False
            score = 0
            health = MAX_HEALTH
            double_shot = False
            double_shot_timer = 0
            enemies.clear()
            bullets.clear()
            particles.clear()
            powerups.clear()

    if not game_over:
        # --- Таймер двойного выстрела ---
        if double_shot:
            double_shot_timer -= 1
            if double_shot_timer <= 0:
                double_shot = False

        # --- Управление (Тач) ---
        touch_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            target_x = touch_pos[0]
            player_x += (target_x - player_x) * player_speed

        player_x = max(player_size, min(WIDTH - player_size, player_x))

        # --- Задний план: Звезды ---
        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, STAR_COLOR, (int(star["x"]), int(star["y"])), 1)

        # --- Автоматическая стрельба ---
        reload_counter += 1
        if reload_counter >= reload_time:
            if double_shot:
                # Спавним две пули по бокам корабля
                offset = player_size // 3
                bullets.append({"x": player_x - offset, "y": player_y - player_size // 2})
                bullets.append({"x": player_x + offset, "y": player_y - player_size // 2})
            else:
                # Обычная пуля по центру
                bullets.append({"x": player_x, "y": player_y - player_size // 2})
            reload_counter = 0

        # Движение пуль
        for b in bullets[:]:
            b["y"] -= bullet_speed
            if b["y"] < 0:
                bullets.remove(b)

        # --- Спавн Врагов ---
        spawn_counter += 1
        if spawn_counter >= spawn_rate:
            e_size = random.randint(int(WIDTH * 0.06), int(WIDTH * 0.12))
            enemies.append({
                "rect": pygame.Rect(random.randint(0, WIDTH - e_size), -e_size, e_size, e_size),
                "speed": random.uniform(enemy_speed_min, enemy_speed_max),
                "color": ENEMY_COLOR
            })
            spawn_counter = 0

        # Движение врагов и урон за пропуск
        player_rect = pygame.Rect(player_x - player_size//2, player_y - player_size//2, player_size, player_size)
        for e in enemies[:]:
            e["rect"].y += e["speed"]
            
            # БАГ ФИКС: Если враг улетел за экран -> теряем жизнь
            if e["rect"].y > HEIGHT:
                enemies.remove(e)
                health -= 1
                if health <= 0:
                    game_over = True
                continue

            # Столкновение врага с игроком
            if e["rect"].colliderect(player_rect):
                create_explosion(player_x, player_y, PLAYER_COLOR)
                create_explosion(e["rect"].centerx, e["rect"].centery, ENEMY_COLOR)
                enemies.remove(e)
                health -= 1
                if health <= 0:
                    game_over = True

        # --- Проверка попаданий (Пуля во Врага) ---
        for b in bullets[:]:
            b_rect = pygame.Rect(b["x"] - 3, b["y"] - 10, 6, 20)
            for e in enemies[:]:
                if e["rect"].colliderect(b_rect):
                    create_explosion(e["rect"].centerx, e["rect"].centery, ENEMY_COLOR)
                    
                    # ШАНС СПАВНА УЛУЧШЕНИЙ (20%)
                    if random.random() < 0.20:
                        p_type = random.choice(['heal', 'double'])
                        p_color = HEALTH_COLOR if p_type == 'heal' else POW_DOUBLE_COLOR
                        powerups.append({
                            "x": e["rect"].centerx,
                            "y": e["rect"].centery,
                            "radius": int(WIDTH * 0.035),
                            "type": p_type,
                            "color": p_color
                        })

                    if b in bullets: bullets.remove(b)
                    if e in enemies: enemies.remove(e)
                    score += 10
                    break

        # --- Логика и Отрисовка Улучшений (Сферы) ---
        for p in powerups[:]:
            p["y"] += powerup_speed
            if p["y"] > HEIGHT:
                powerups.remove(p)
                continue

            # Проверка подбора игроком
            p_rect = pygame.Rect(p["x"] - p["radius"], p["y"] - p["radius"], p["radius"]*2, p["radius"]*2)
            if p_rect.colliderect(player_rect):
                create_explosion(p["x"], p["y"], p["color"])
                if p["type"] == 'heal':
                    health = min(MAX_HEALTH, health + 1) # Лечим, но не выше максимума
                elif p["type"] == 'double':
                    double_shot = True
                    double_shot_timer = 420 # 7 секунд работы (60 FPS * 7)
                powerups.remove(p)
                continue

            # Отрисовка сферы с эффектом неонового свечения
            pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), p["radius"], 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(p["x"]), int(p["y"])), int(p["radius"] * 0.4))

        # --- Отрисовка Частиц (Взрывы) ---
        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.04
            if p["life"] <= 0:
                particles.remove(p)
            else:
                alpha_color = [max(0, min(255, int(c * p["life"]))) for c in p["color"]]
                pygame.draw.circle(screen, alpha_color, (int(p["x"]), int(p["y"])), int(p["radius"] * 1.5), 1)
                pygame.draw.circle(screen, (255, 255, 255), (int(p["x"]), int(p["y"])), int(p["radius"] * 0.5))

        # --- Рендеринг Игрока ---
        pt1 = (player_x, player_y - player_size // 2)
        pt2 = (player_x - player_size // 2, player_y + player_size // 2)
        pt3 = (player_x + player_size // 2, player_y + player_size // 2)
        pygame.draw.polygon(screen, PLAYER_COLOR, [pt1, pt2, pt3], 3)
        pygame.draw.polygon(screen, (255, 255, 255), [pt1, pt2, pt3], 0)

        # --- Рендеринг Пуль ---
        for b in bullets:
            pygame.draw.line(screen, BULLET_COLOR, (b["x"], b["y"]), (b["x"], b["y"] - 15), 4)

        # --- Рендеринг Врагов ---
        for e in enemies:
            pygame.draw.rect(screen, e["color"], e["rect"], 3)
            pygame.draw.rect(screen, (255, 255, 255), e["rect"].inflate(-6, -6), 1)

        # --- Интерфейс (UI) ---
        font = pygame.font.SysFont(None, int(WIDTH * 0.07))
        
        # Счет
        score_txt = font.render(f"SCORE: {score}", True, (255, 255, 255))
        screen.blit(score_txt, (20, 40))

        # Полоса Здоровья (HP BAR)
        bar_width = int(WIDTH * 0.35)
        bar_height = int(HEIGHT * 0.018)
        bar_x = WIDTH - bar_width - 20
        bar_y = 40
        # Рамка хелсбара
        pygame.draw.rect(screen, (60, 60, 80), (bar_x, bar_y, bar_width, bar_height), 2)
        # Заполнение хелсбара
        if health > 0:
            fill_width = int(bar_width * (health / MAX_HEALTH))
            pygame.draw.rect(screen, HEALTH_COLOR, (bar_x, bar_y, fill_width, bar_height))

        # Индикатор двойного выстрела (если активен)
        if double_shot:
            p_font = pygame.font.SysFont(None, int(WIDTH * 0.05))
            boost_txt = p_font.render("DOUBLE SHOT ACTIVE", True, POW_DOUBLE_COLOR)
            screen.blit(boost_txt, (WIDTH - boost_txt.get_width() - 20, bar_y + bar_height + 10))

    else:
        # --- Экран GAME OVER ---
        font_big = pygame.font.SysFont(None, int(WIDTH * 0.15))
        font_small = pygame.font.SysFont(None, int(WIDTH * 0.06))
        
        go_txt = font_big.render("GAME OVER", True, ENEMY_COLOR)
        final_score = font_small.render(f"TOTAL SCORE: {score}", True, (255, 255, 255))
        restart_txt = font_small.render("TAP TO RESTART", True, PLAYER_COLOR)
        
        screen.blit(go_txt, (WIDTH // 2 - go_txt.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(final_score, (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2))
        screen.blit(restart_txt, (WIDTH // 2 - restart_txt.get_width() // 2, HEIGHT // 2 + 80))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
