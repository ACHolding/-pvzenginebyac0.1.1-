# import python 3.14  <-- Future proofing for 2026+
import pygame
import sys
import random
import time
import math
import array

# ================================================
# AC's PVZ 1.x
# 60 FPS • HD 600x400 • Pure Pygame
# [C] Ac holdings [C] popcap
# ================================================

# --- ENGINE CONFIGURATION ---
# 60 FPS lock • Windows XP speed (speed_mult 1.0 = original feel)
ENGINE_CONFIG = {
    "title": "AC's PVZ 1.x",
    "width": 600,
    "height": 400,
    "fps": 60,
    "os_profile": "Windows XP",
    "speed_mult": 1.0   # Windows XP speed @ 60 FPS
}

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.joystick.init()

WIDTH, HEIGHT = ENGINE_CONFIG["width"], ENGINE_CONFIG["height"]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(ENGINE_CONFIG["title"])
clock = pygame.time.Clock()

# --- ENGINE PALETTE ---
FLASH_GRASS_1 = (107, 199, 67)
FLASH_GRASS_2 = (90, 180, 50)
FLASH_DIRT = (139, 90, 43)
FLASH_SKY = (140, 210, 255)
FLASH_YELLOW = (255, 240, 0)
FLASH_GREEN = (40, 180, 60)
FLASH_DARK_GREEN = (25, 130, 40)
FLASH_RED = (255, 50, 50)
FLASH_WHITE = (255, 255, 255)
FLASH_BLACK = (0, 0, 0)
FLASH_WOOD = (139, 69, 19)
FLASH_WOOD_DARK = (101, 42, 14)
FLASH_STONE = (160, 160, 160)
FLASH_STONE_DARK = (100, 100, 100)

# --- ENGINE LAYOUT ---
GRID_COLS = 9
GRID_ROWS = 5
CELL_W = 38
CELL_H = 47
LAWN_X = 95
LAWN_Y = 88

# --- ENGINE ASSETS (Fonts) ---
font_huge = pygame.font.SysFont("arialblack", 45)
font_big = pygame.font.SysFont("arialblack", 18)
font_small = pygame.font.SysFont("arialblack", 13)
font_tiny = pygame.font.SysFont("arial", 9)

# Controller
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
cursor_x = WIDTH // 2
cursor_y = HEIGHT // 2

# ===================== PVZ REPLANTED VOICE BANK (FM & Envelope Math Synthesis) =====================
# Real audio generated using advanced mathematical equations (Harmonics, Envelopes, FM synthesis)
def create_sound(freq_start, freq_end, duration, vol, wave_type='sine'):
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n_samples):
            t = float(i) / sample_rate
            progress = i / n_samples
            
            # Pitch slide interpolation
            freq = freq_start + (freq_end - freq_start) * progress
            angle = 2.0 * math.pi * freq * t
            
            # Volume Envelope (Attack and Decay) to make it sound "real" and avoid clicking
            env = 1.0
            attack_time = 0.05
            if progress < attack_time:
                env = progress / attack_time
            else:
                # Exponential decay for natural fade out
                env = math.exp(-4.0 * (progress - attack_time))
            
            # Synthesis Algorithms using pure Math
            if wave_type == 'sine':
                val = math.sin(angle)
            elif wave_type == 'square':
                val = 1.0 if math.sin(angle) > 0 else -1.0
            elif wave_type == 'saw':
                saw = 2.0 * (freq * t - math.floor(freq * t)) - 1.0
                val = max(-1.0, min(1.0, saw))
            elif wave_type == 'noise':
                val = random.uniform(-1.0, 1.0)
            elif wave_type == 'voice':
                # FM Synthesis (Frequency Modulation) to emulate vocal formants (zombies/dave)
                modulator = math.sin(angle * 1.5) * 2.5
                val = math.sin(angle + modulator)
            elif wave_type == 'bell':
                # Additive Synthesis (Fundamental + Harmonics) for Sun drops & waves
                val = (math.sin(angle) + 0.5 * math.sin(angle * 2.0) + 0.25 * math.sin(angle * 3.0)) / 1.75
            elif wave_type == 'splat':
                # Layered noise + thud for impacts/planting
                val = (math.sin(angle) * 0.6) + (random.uniform(-1.0, 1.0) * 0.4)
            elif wave_type == 'bleep':
                # Short punchy bleep for peas firing / hitting (fast attack, quick decay)
                bleep_env = math.exp(-8.0 * progress) if progress > 0.02 else (progress / 0.02)
                val = bleep_env * math.sin(angle)
            elif wave_type == 'brains':
                # Zombie "BRAAAINS" moan: low rumble + formant wobble
                rumble = math.sin(angle) * 0.7
                formant = math.sin(angle * 2.3 + math.sin(angle * 0.7) * 3) * 0.3
                val = rumble + formant
            else:
                val = 0.0
            
            # Apply volume, envelope and convert to 16-bit PCM Audio format
            final_val = int(vol * env * 32767.0 * val)
            final_val = max(-32768, min(32767, final_val))
            
            buf.append(final_val) # Left channel
            buf.append(final_val) # Right channel
            
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

# Advanced procedural math real audio library (0 files needed)
# BRAINS = zombie moans; pea_bleep / pea_hit = peas bleepping
engine_sfx = {
    "plant": create_sound(200, 50, 0.15, 0.5, 'splat'),
    "sun": create_sound(800, 1200, 0.3, 0.4, 'bell'),
    "shoot": create_sound(600, 400, 0.1, 0.3, 'square'),
    "splat": create_sound(150, 50, 0.2, 0.5, 'splat'),
    "groan": create_sound(120, 80, 0.8, 0.6, 'voice'),
    # BRAINS voice bank — zombie "braaaaains" moans (variants for variety)
    "brains": create_sound(95, 55, 1.0, 0.65, 'brains'),
    "brains2": create_sound(85, 50, 1.1, 0.6, 'brains'),
    "brains3": create_sound(75, 45, 0.9, 0.6, 'brains'),
    # Peas bleepping — pea fire + pea hit
    "pea_bleep": create_sound(980, 720, 0.07, 0.4, 'bleep'),
    "pea_hit": create_sound(420, 180, 0.1, 0.45, 'bleep'),
    "ready": create_sound(400, 400, 0.4, 0.5, 'bell'),
    "set": create_sound(400, 400, 0.4, 0.5, 'bell'),
    "plant_shout": create_sound(600, 800, 0.5, 0.6, 'voice'),
    "buzzer": create_sound(100, 100, 0.3, 0.5, 'saw'),
    "click": create_sound(600, 400, 0.05, 0.35, 'sine'),
    "lawnmower": create_sound(80, 60, 0.5, 0.5, 'saw'),
    "wave": create_sound(200, 350, 0.6, 0.4, 'bell'),
    "win": create_sound(523, 1047, 0.5, 0.5, 'bell'),
}

def play_sfx(name):
    if engine_sfx.get(name):
        engine_sfx[name].play()

# ===================== ENGINE ENTITIES =====================
class CrazyDave:
    def __init__(self):
        self.x = 35
        self.y = 170
        self.bob = 0
        self.talk_timer = 0
        self.mouth_open = False
        self.speeches = ["HOWDY NEIGHBOR!", "PLANT SOME PEAS!", "ZOMBIES COMING!", "BRAINZ BAD!", "HEY LISTEN!"]

    def update(self):
        self.bob = math.sin(time.time() * 3 * ENGINE_CONFIG["speed_mult"]) * 3
        self.talk_timer += 1 * ENGINE_CONFIG["speed_mult"]
        if int(self.talk_timer) % 25 == 0:
            self.mouth_open = not self.mouth_open

    def draw(self, surf):
        y = self.y + self.bob
        pygame.draw.rect(surf, (120, 60, 30), (self.x + 8, y + 38, 36, 48))
        pygame.draw.ellipse(surf, (220, 180, 120), (self.x + 10, y + 8, 34, 38))
        pygame.draw.rect(surf, (0, 120, 40), (self.x + 6, y + 2, 40, 12))
        pygame.draw.rect(surf, (0, 100, 30), (self.x + 14, y - 4, 26, 8))
        pygame.draw.circle(surf, FLASH_WHITE, (self.x + 19, y + 20), 6)
        pygame.draw.circle(surf, FLASH_WHITE, (self.x + 31, y + 20), 6)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x + 19, y + 21), 3)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x + 31, y + 21), 3)
        
        mouth_y = y + 30 if self.mouth_open else y + 28
        pygame.draw.arc(surf, FLASH_BLACK, (self.x + 19, mouth_y, 14, 7), 0, 3.14, 3)
        pygame.draw.ellipse(surf, (80, 60, 40), (self.x + 14, y + 30, 24, 14))

        if int(self.talk_timer) % 180 < 90:
            bubble_x = self.x + 58
            pygame.draw.ellipse(surf, FLASH_WHITE, (bubble_x - 2, y - 12, 88, 32))
            pygame.draw.polygon(surf, FLASH_WHITE, [(bubble_x + 2, y + 12), (bubble_x - 8, y + 18), (bubble_x + 8, y + 22)])
            txt = font_tiny.render(self.speeches[int(self.talk_timer) // 120 % len(self.speeches)], True, FLASH_BLACK)
            surf.blit(txt, (bubble_x + 6, y - 5))

class Button:
    def __init__(self, x, y, w, h, text, is_wood=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.is_wood = is_wood
        self.hover = False

    def draw(self, surf):
        if self.is_wood:
            color = (160, 80, 30) if self.hover else FLASH_WOOD
            pygame.draw.rect(surf, color, self.rect, border_radius=8)
            pygame.draw.rect(surf, FLASH_WOOD_DARK, self.rect, 3, border_radius=8)
            txt_color = (255, 255, 200)
        else:
            color = (60, 200, 80) if self.hover else FLASH_GREEN
            pygame.draw.rect(surf, color, self.rect, border_radius=12)
            pygame.draw.rect(surf, FLASH_WHITE, self.rect, 4, border_radius=12)
            txt_color = FLASH_BLACK
        txt = font_big.render(self.text, True, txt_color)
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def update(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover

class Plant:
    def __init__(self, col, row, hp):
        self.col = col
        self.row = row
        self.x = LAWN_X + col * CELL_W + CELL_W // 2
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.hp = hp
        self.max_hp = hp
        self.timer = 0

class Peashooter(Plant):
    def __init__(self, col, row):
        super().__init__(col, row, 100)
    def update(self):
        self.timer += 1 * ENGINE_CONFIG["speed_mult"]
        if self.timer >= 90:
            if any(z.row == self.row and z.x > self.x for z in zombies):
                peas.append(Pea(self.x + 10, self.y - 10))
                play_sfx("pea_bleep")
                self.timer = 0
    def draw(self, surf):
        pygame.draw.circle(surf, FLASH_GREEN, (self.x, self.y), 14)
        pygame.draw.rect(surf, FLASH_GREEN, (self.x, self.y - 14, 20, 10))
        pygame.draw.circle(surf, FLASH_BLACK, (self.x + 4, self.y - 4), 3)

class Sunflower(Plant):
    def __init__(self, col, row):
        super().__init__(col, row, 100)
    def update(self):
        self.timer += 1 * ENGINE_CONFIG["speed_mult"]
        if self.timer >= 420:
            suns.append(Sun(self.x + random.randint(-15, 15), self.y - 10))
            self.timer = 0
    def draw(self, surf):
        pygame.draw.circle(surf, (255, 150, 0), (self.x, self.y), 16)
        pygame.draw.circle(surf, FLASH_YELLOW, (self.x, self.y), 12)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x - 4, self.y - 2), 2)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x + 4, self.y - 2), 2)

class WallNut(Plant):
    def __init__(self, col, row):
        super().__init__(col, row, 500)
    def update(self):
        pass
    def draw(self, surf):
        color = (180, 130, 40) if self.hp > 250 else (140, 90, 30)
        pygame.draw.ellipse(surf, color, (self.x - 14, self.y - 18, 28, 36))
        pygame.draw.circle(surf, FLASH_BLACK, (self.x - 5, self.y - 5), 3)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x + 5, self.y - 5), 3)

class Zombie:
    def __init__(self, row, is_cone):
        self.row = row
        self.x = WIDTH + 20
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.is_cone = is_cone
        self.health = 200 if is_cone else 100
        self.speed = 0.3 * ENGINE_CONFIG["speed_mult"]
        self.eat_timer = 0

    def update(self):
        target_plant = None
        for p in plants:
            if p.row == self.row and abs(p.x - self.x) < 20:
                target_plant = p
                break

        if target_plant:
            self.eat_timer += 1 * ENGINE_CONFIG["speed_mult"]
            if self.eat_timer > 30:
                target_plant.hp -= 10
                self.eat_timer = 0
                play_sfx("splat")
                if target_plant.hp <= 0 and target_plant in plants:
                    plants.remove(target_plant)
        else:
            self.x -= self.speed
            self.eat_timer = 0

    def draw(self, surf):
        pygame.draw.rect(surf, (100, 100, 100), (self.x - 10, self.y - 20, 20, 40))
        pygame.draw.circle(surf, (100, 150, 100), (self.x, self.y - 25), 12)
        pygame.draw.circle(surf, FLASH_BLACK, (self.x - 4, self.y - 27), 2)
        if self.is_cone:
            pygame.draw.polygon(surf, (255, 120, 0), [(self.x - 12, self.y - 30), (self.x, self.y - 55), (self.x + 12, self.y - 30)])

class Pea:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 4 * ENGINE_CONFIG["speed_mult"]
    def update(self):
        self.x += self.speed
        return self.x > WIDTH 
    def draw(self, surf):
        pygame.draw.circle(surf, (150, 255, 150), (self.x, self.y), 6)

class Sun:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_y = random.randint(LAWN_Y, HEIGHT - 30)
        self.speed = 1 * ENGINE_CONFIG["speed_mult"]
    def update(self):
        if self.y < self.target_y:
            self.y += self.speed
    def draw(self, surf):
        pygame.draw.circle(surf, (255, 150, 0), (self.x, self.y), 16)
        pygame.draw.circle(surf, FLASH_YELLOW, (self.x, self.y), 12)

class Lawnmower:
    def __init__(self, row):
        self.row = row
        self.x = LAWN_X - 35
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.active = False
        self.used = False
        self.speed = 6 * ENGINE_CONFIG["speed_mult"]
    def update(self):
        if self.active:
            self.x += self.speed
            if self.x > WIDTH:
                self.used = True
    def draw(self, surf):
        if not self.used:
            pygame.draw.rect(surf, FLASH_RED, (self.x - 10, self.y - 10, 24, 20))
            pygame.draw.circle(surf, FLASH_BLACK, (self.x - 5, self.y + 10), 6)
            pygame.draw.circle(surf, FLASH_BLACK, (self.x + 10, self.y + 10), 6)

# ===================== ENGINE STATE =====================
sun_count = 50
plants = []
zombies = []
peas = []
suns = []
lawnmowers = []
score = 0
wave = 1
game_state = "MENU"
selected_plant = None
ready_timer = 0
ready_step = 0

crazy_dave = CrazyDave()

play_btn = Button(320, 110, 180, 40, "ADVENTURE", is_wood=True)
mini_btn = Button(320, 165, 180, 40, "MINI-GAMES", is_wood=True)
almanac_btn = Button(320, 220, 180, 40, "ALMANAC", is_wood=True)
controls_btn = Button(320, 275, 180, 40, "CONTROLS", is_wood=True)
quit_btn = Button(320, 330, 180, 40, "QUIT", is_wood=True)
menu_btn = Button(WIDTH//2 - 90, HEIGHT - 60, 180, 40, "BACK TO MENU", is_wood=True)

seed_rects = {
    "PEASHOOTER": pygame.Rect(95, 12, 42, 58),
    "SUNFLOWER": pygame.Rect(143, 12, 42, 58),
    "WALLNUT": pygame.Rect(191, 12, 42, 58)
}
seed_costs = {"PEASHOOTER": 100, "SUNFLOWER": 50, "WALLNUT": 50}
shovel_rect = pygame.Rect(285, 18, 24, 48)

def spawn_zombie_wave():
    global wave
    num = (wave // 2) + 1
    for _ in range(num):
        is_cone = random.random() < 0.3 and wave > 2
        zombies.append(Zombie(random.randint(0, GRID_ROWS-1), is_cone))
    wave += 1

def reset_game():
    global sun_count, plants, zombies, peas, suns, lawnmowers, score, wave, ready_timer, ready_step, selected_plant
    sun_count = 50
    plants.clear()
    zombies.clear()
    peas.clear()
    suns.clear()
    lawnmowers = [Lawnmower(r) for r in range(GRID_ROWS)]
    score = 0
    wave = 1
    ready_timer = 0
    ready_step = 0
    selected_plant = None

# ===================== ENGINE RENDERING =====================
def draw_main_menu(surf):
    surf.fill(FLASH_SKY)
    pygame.draw.rect(surf, FLASH_GRASS_1, (0, HEIGHT//2, WIDTH, HEIGHT//2))
    pygame.draw.rect(surf, (200, 180, 150), (50, 120, 175, 150))
    pygame.draw.polygon(surf, (150, 50, 50), [(30, 120), (137, 25), (235, 120)])
    
    t_rect = pygame.Rect(95, 25, 225, 110)
    pygame.draw.rect(surf, FLASH_STONE, t_rect, border_radius=20)
    pygame.draw.rect(surf, FLASH_STONE_DARK, t_rect, 4, border_radius=20)
    t1 = font_big.render("AC'S PVZ 1.x", True, FLASH_BLACK)
    surf.blit(t1, (t_rect.centerx - t1.get_width()//2, 55))

    copy_txt = font_tiny.render("[C] Ac holdings [C] popcap", True, FLASH_WHITE)
    surf.blit(copy_txt, (WIDTH - copy_txt.get_width() - 10, HEIGHT - 15))

    crazy_dave.update()
    crazy_dave.draw(surf)

    play_btn.draw(surf)
    mini_btn.draw(surf)
    almanac_btn.draw(surf)
    controls_btn.draw(surf)
    quit_btn.draw(surf)

def draw_controls_screen(surf):
    surf.fill((220, 235, 255))
    pygame.draw.rect(surf, FLASH_WOOD, (30, 20, WIDTH - 60, HEIGHT - 80), border_radius=12)
    pygame.draw.rect(surf, FLASH_WOOD_DARK, (30, 20, WIDTH - 60, HEIGHT - 80), 4, border_radius=12)
    title = font_big.render("HOW TO PLAY — PVZ REPLANTED", True, FLASH_BLACK)
    surf.blit(title, (WIDTH//2 - title.get_width()//2, 35))
    lines = [
        "MOUSE: Move cursor. Click seed packet to select, then click lawn to plant.",
        "CLICK SUN: Collect falling sun for more sun (currency).",
        "SHOVEL: Select shovel, then click a plant to remove it.",
        "PEASHOOTER (100): Shoots peas at zombies in same row.",
        "SUNFLOWER (50): Produces sun over time.",
        "WALL-NUT (50): High HP blocker. Survives many bites.",
        "LAWN MOWERS: Activate when a zombie reaches the left; they clear the row.",
        "ESC: Pause / return to main menu from any screen.",
    ]
    y = 70
    for line in lines:
        txt = font_small.render(line, True, FLASH_BLACK)
        surf.blit(txt, (50, y))
        y += 28
    esc_hint = font_tiny.render("Press ESC or click BACK TO MENU to return.", True, FLASH_BLACK)
    surf.blit(esc_hint, (WIDTH//2 - esc_hint.get_width()//2, HEIGHT - 55))

def draw_lawn(surf):
    surf.fill(FLASH_SKY)
    pygame.draw.rect(surf, (180, 150, 120), (0, 0, LAWN_X - 35, HEIGHT))
    pygame.draw.rect(surf, FLASH_DIRT, (LAWN_X - 35, LAWN_Y, 35, GRID_ROWS * CELL_H))
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            color = FLASH_GRASS_1 if (r + c) % 2 == 0 else FLASH_GRASS_2
            pygame.draw.rect(surf, color, (LAWN_X + c * CELL_W, LAWN_Y + r * CELL_H, CELL_W, CELL_H))

def draw_engine_hud(surf):
    pygame.draw.rect(surf, FLASH_WOOD, (82, 6, 210, 70), border_radius=12)
    pygame.draw.rect(surf, FLASH_WOOD_DARK, (82, 6, 210, 70), 6, border_radius=12)

    pygame.draw.rect(surf, (139, 69, 19), (8, 8, 68, 62), border_radius=12)
    pygame.draw.rect(surf, FLASH_WOOD_DARK, (8, 8, 68, 62), 4, border_radius=12)
    pygame.draw.circle(surf, FLASH_YELLOW, (42, 29), 14)
    sun_txt = font_big.render(str(sun_count), True, FLASH_YELLOW)
    surf.blit(sun_txt, (42 - sun_txt.get_width()//2, 44))

    for i, (name, base_rect) in enumerate(seed_rects.items()):
        r = base_rect.copy()
        color = (220, 190, 110) if sun_count >= seed_costs[name] else (120, 100, 70)
        pygame.draw.rect(surf, color, r, border_radius=8)
        pygame.draw.rect(surf, FLASH_WHITE if selected_plant == name else FLASH_BLACK, r, 4, border_radius=8)
        
        if name == "PEASHOOTER":
            pygame.draw.circle(surf, FLASH_GREEN, (r.centerx, r.centery - 10), 12)
        elif name == "SUNFLOWER":
            pygame.draw.circle(surf, FLASH_YELLOW, (r.centerx, r.centery - 10), 12)
        elif name == "WALLNUT":
            pygame.draw.ellipse(surf, (180, 130, 40), (r.centerx - 9, r.centery - 15, 18, 22))
        
        cost_txt = font_tiny.render(str(seed_costs[name]), True, FLASH_BLACK)
        surf.blit(cost_txt, (r.right - 14, r.bottom - 12))

    shovel_color = (150, 150, 150) if selected_plant == "SHOVEL" else (110, 110, 110)
    pygame.draw.rect(surf, shovel_color, shovel_rect)
    pygame.draw.polygon(surf, (200, 200, 200), [(288, 19), (300, 19), (305, 28), (292, 38)])

    pygame.draw.rect(surf, (80, 50, 30), (WIDTH - 105, HEIGHT - 32, 95, 24), border_radius=6)
    wave_txt = font_small.render(f"WAVE {wave}", True, FLASH_YELLOW)
    surf.blit(wave_txt, (WIDTH - 90, HEIGHT - 28))
    esc_hint = font_tiny.render("ESC = Menu", True, FLASH_WHITE)
    surf.blit(esc_hint, (WIDTH - 105, 8))

# ===================== ENGINE MAIN LOOP =====================
running = True
last_wave_time = time.time()
sun_spawn_timer = 0

reset_game()

while running:
    clock.tick(ENGINE_CONFIG["fps"])
    mx, my = pygame.mouse.get_pos()

    for j in joysticks:
        axis_x = j.get_axis(0)
        axis_y = j.get_axis(1)
        if abs(axis_x) > 0.1: cursor_x += axis_x * 12
        if abs(axis_y) > 0.1: cursor_y += axis_y * 12
        cursor_x = max(0, min(WIDTH, cursor_x))
        cursor_y = max(0, min(HEIGHT, cursor_y))

    click = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # ESC = always return to main menu (PVZ Replanted style)
            game_state = "MENU"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True
        if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
            click = True
            mx, my = cursor_x, cursor_y

    if game_state == "MENU":
        play_btn.update((mx, my))
        mini_btn.update((mx, my))
        almanac_btn.update((mx, my))
        controls_btn.update((mx, my))
        quit_btn.update((mx, my))

        if click:
            if play_btn.hover:
                reset_game()
                game_state = "READY_SET_PLANT"
                play_sfx("plant")
            elif mini_btn.hover:
                game_state = "MINI_GAMES"
                play_sfx("plant")
            elif almanac_btn.hover:
                game_state = "ALMANAC"
                play_sfx("plant")
            elif controls_btn.hover:
                game_state = "CONTROLS"
                play_sfx("click")
            elif quit_btn.hover:
                running = False
            else:
                play_sfx("buzzer")

        draw_main_menu(screen)

    elif game_state == "CONTROLS":
        draw_controls_screen(screen)
        menu_btn.update((mx, my))
        menu_btn.draw(screen)
        if click and menu_btn.hover:
            game_state = "MENU"

    elif game_state == "MINI_GAMES":
        screen.fill(FLASH_SKY)
        txt = font_huge.render("MINI-GAMES", True, FLASH_BLACK)
        sub = font_big.render("(AC'S Engine Extension)", True, FLASH_BLACK)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//3))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2))
        menu_btn.update((mx, my))
        menu_btn.draw(screen)
        if click and menu_btn.hover:
            game_state = "MENU"

    elif game_state == "ALMANAC":
        screen.fill((200, 200, 150))
        txt = font_huge.render("ALMANAC", True, FLASH_BLACK)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 50))
        info = font_big.render("Zombies want Brainz. Plants want Sun.", True, FLASH_BLACK)
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2))
        menu_btn.update((mx, my))
        menu_btn.draw(screen)
        if click and menu_btn.hover:
            game_state = "MENU"

    elif game_state == "READY_SET_PLANT":
        draw_lawn(screen)
        draw_engine_hud(screen)
        ready_timer += 1 * ENGINE_CONFIG["speed_mult"]

        # Play math-synthesized voice bank audio once per word (Ready / Set / Plant)
        if ready_timer < 60:
            if ready_step == 0:
                play_sfx("ready")
                ready_step = 1
            text = "READY!"
        elif ready_timer < 120:
            if ready_step == 1:
                play_sfx("set")
                ready_step = 2
            text = "SET!"
        elif ready_timer < 180:
            if ready_step == 2:
                play_sfx("plant_shout")
                ready_step = 3
            text = "PLANT!"
        else:
            game_state = "PLAYING"
            last_wave_time = time.time()
            text = ""

        if text:
            txt_surf = font_huge.render(text, True, FLASH_RED)
            pygame.draw.rect(screen, (0,0,0,150), (WIDTH//2 - txt_surf.get_width()//2 - 10, HEIGHT//2 - txt_surf.get_height()//2 - 10, txt_surf.get_width() + 20, txt_surf.get_height() + 20))
            screen.blit(txt_surf, (WIDTH//2 - txt_surf.get_width()//2, HEIGHT//2 - txt_surf.get_height()//2))

    elif game_state == "PLAYING":
        sun_spawn_timer += 1 * ENGINE_CONFIG["speed_mult"]
        if sun_spawn_timer > 400:
            suns.append(Sun(random.randint(LAWN_X + 25, LAWN_X + GRID_COLS * CELL_W - 25), -15))
            sun_spawn_timer = 0
            
        # Spawn wave dynamically adjusted by OS Speed multiplier emulation
        adjusted_wave_time = 15 / ENGINE_CONFIG["speed_mult"]
        if time.time() - last_wave_time > adjusted_wave_time:
            spawn_zombie_wave()
            play_sfx("wave")
            last_wave_time = time.time()

        for p in plants: p.update()
        for s in suns: s.update()
        
        for z in zombies[:]:
            z.update()
            if z.x < 0:
                game_state = "GAME_OVER"
                play_sfx(random.choice(["brains", "brains2", "brains3"]))

        for p in peas[:]:
            if p.update():
                if p in peas:
                    peas.remove(p)
            else:
                for z in zombies[:]:
                    if z.row != (p.y - LAWN_Y) // CELL_H:
                        continue
                    hit_dist_x = abs(z.x - p.x)
                    hit_dist_y = abs((z.y - 15) - p.y)  # aim roughly at zombie head/chest
                    if hit_dist_x < 38 and hit_dist_y < 22:
                        play_sfx("pea_hit")
                        z.health -= 20
                        if p in peas:
                            peas.remove(p)
                        if z.health <= 0 and z in zombies:
                            zombies.remove(z)
                            score += 10
                        break
        
        for m in lawnmowers:
            m.update()
            if not m.active and not m.used:
                for z in zombies:
                    if z.row == m.row and z.x < m.x + 20:
                        m.active = True
                        play_sfx("ready")
                        break
            if m.active:
                for z in zombies[:]:
                    if z.row == m.row and abs(z.x - m.x) < 30:
                        if z in zombies:
                            zombies.remove(z)
                            score += 10

        if click:
            sun_collected = False
            for s in suns[:]:
                if (mx - s.x)**2 + (my - s.y)**2 < 400:
                    sun_count += 25
                    play_sfx("sun")
                    suns.remove(s)
                    sun_collected = True
                    break
            
            if not sun_collected:
                clicked_ui = False
                for name, rect in seed_rects.items():
                    if rect.collidepoint(mx, my):
                        if sun_count >= seed_costs[name]:
                            selected_plant = name
                            play_sfx("plant")
                        clicked_ui = True
                        break
                
                if shovel_rect.collidepoint(mx, my):
                    selected_plant = "SHOVEL"
                    clicked_ui = True

                if not clicked_ui and selected_plant:
                    col = (mx - LAWN_X) // CELL_W
                    row = (my - LAWN_Y) // CELL_H
                    if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                        target_plant = next((p for p in plants if p.col == col and p.row == row), None)
                        
                        if selected_plant == "SHOVEL":
                            if target_plant:
                                plants.remove(target_plant)
                                play_sfx("splat")
                            selected_plant = None
                        elif not target_plant:
                            cost = seed_costs.get(selected_plant, 0)
                            if sun_count >= cost:
                                play_sfx("plant")
                                if selected_plant == "PEASHOOTER": plants.append(Peashooter(col, row))
                                elif selected_plant == "SUNFLOWER": plants.append(Sunflower(col, row))
                                elif selected_plant == "WALLNUT": plants.append(WallNut(col, row))
                                sun_count -= cost
                                selected_plant = None
                    else:
                        selected_plant = None

        draw_lawn(screen)
        for m in lawnmowers: m.draw(screen)
        for p in plants: p.draw(screen)
        for z in zombies: z.draw(screen)
        for p in peas: p.draw(screen)
        for s in suns: s.draw(screen)
        draw_engine_hud(screen)

        if selected_plant and selected_plant != "SHOVEL":
            pygame.draw.circle(screen, (255, 255, 255, 128), (mx, my), 15)
        elif selected_plant == "SHOVEL":
            pygame.draw.polygon(screen, FLASH_RED, [(mx, my), (mx+10, my+10), (mx+15, my+20), (mx+5, my+30)])

    elif game_state == "GAME_OVER":
        screen.fill(FLASH_BLACK)
        txt = font_huge.render("THE ZOMBIES ATE YOUR BRAINS!", True, FLASH_RED)
        score_txt = font_big.render(f"Final Score: {score}  |  Wave Reached: {wave}", True, FLASH_WHITE)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//3))
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, HEIGHT//2))
        esc_txt = font_small.render("ESC or BACK TO MENU = Main Menu", True, FLASH_YELLOW)
        screen.blit(esc_txt, (WIDTH//2 - esc_txt.get_width()//2, HEIGHT//2 + 45))
        menu_btn.update((mx, my))
        menu_btn.draw(screen)
        if click and menu_btn.hover:
            game_state = "MENU"

    pygame.display.flip()

pygame.quit()
sys.exit()
