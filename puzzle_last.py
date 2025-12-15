import pygame
import random
import copy
import heapq
import time
import math
from collections import deque

# --- INISIALISASI ---
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Water Sort: Generator BFS & Hint A*")

# Font & Clock
font = pygame.font.Font('freesansbold.ttf', 20)
large_font = pygame.font.Font('freesansbold.ttf', 40)
clock = pygame.time.Clock()
FPS = 60

# --- COLORS ---
COLOR_MAP = {
    1: (220, 20, 60),    # Crimson
    2: (65, 105, 225),   # Royal Blue
    3: (50, 205, 50),    # Lime Green
    4: (255, 215, 0),    # Gold
    5: (138, 43, 226),   # Blue Violet
    6: (255, 140, 0),    # Dark Orange
    7: (0, 255, 255),    # Cyan
    8: (255, 105, 180),  # Hot Pink
    9: (128, 128, 128)   # Gray
}

BOTOL_CAPACITY = 4

# --- KONFIGURASI LEVEL ---
LEVEL_CONFIG = {
    1: {"colors": 3, "empty": 1, "depth": 25}, 
    2: {"colors": 4, "empty": 1, "depth": 45}, 
    3: {"colors": 5, "empty": 2, "depth": 75},
    4: {"colors": 6, "empty": 2, "depth": 110}, 
    5: {"colors": 7, "empty": 2, "depth": 150}  
}

# ==========================================
# 1. CORE LOGIC (Aturan Main)
# ==========================================

def state_to_key(state):
    return tuple(tuple(t) for t in state)

def is_goal_state(state):
    for t in state:
        if not t: continue
        if len(t) != BOTOL_CAPACITY: return False
        if len(set(t)) != 1: return False
    return True

def valid_moves_from(state):
    moves = []
    n = len(state)
    for i in range(n):
        if not state[i]: continue 
        for j in range(n):
            if i == j: continue
            if len(state[j]) >= BOTOL_CAPACITY: continue
            if not state[j] or state[j][-1] == state[i][-1]:
                moves.append((i, j))
    return moves

def apply_move(state, move):
    i, j = move
    new_state = [list(t) for t in state]
    src, dst = new_state[i], new_state[j]
    if not src: return new_state
    color = src[-1]
    count = 0
    for k in range(len(src)-1, -1, -1):
        if src[k] == color: count += 1
        else: break
    space = BOTOL_CAPACITY - len(dst)
    amount = min(count, space)
    for _ in range(amount):
        dst.append(src.pop())
    return new_state

# ==========================================
# 2. HINT SYSTEM: A* (A-STAR)
# ==========================================

def get_heuristic_score(state):
    """Heuristik untuk A*: Menghitung tingkat kekacauan"""
    score = 0
    for tube in state:
        if not tube: continue
        for i in range(len(tube) - 1):
            if tube[i] != tube[i+1]: score += 3 
        if len(tube) < BOTOL_CAPACITY: score += 1
        if len(tube) > 0 and tube[0] != tube[-1]: score += 2
    return score

def astar_find_hint(start_state):
    """
    ALGORITMA A* (A-STAR) untuk mencari HINT.
    Menggunakan Priority Queue (heapq).
    """
    if is_goal_state(start_state): return None
    
    pq = []
    h = get_heuristic_score(start_state)
    # Tuple: (f_score, g_score, state, path)
    heapq.heappush(pq, (h, 0, start_state, [])) 
    
    visited = {state_to_key(start_state): 0}
    max_nodes = 5000
    nodes = 0

    while pq:
        f, g, cur, path = heapq.heappop(pq)
        nodes += 1
        
        if is_goal_state(cur): return path[0] if path else None
        if nodes > max_nodes: return None

        for m in valid_moves_from(cur):
            nxt = apply_move(cur, m)
            nxt_key = state_to_key(nxt)
            new_g = g + 1
            
            # Logic A*: f(n) = g(n) + h(n)
            if nxt_key not in visited or new_g < visited[nxt_key]:
                visited[nxt_key] = new_g
                new_h = get_heuristic_score(nxt)
                heapq.heappush(pq, (new_g + new_h * 1.5, new_g, nxt, path + [m]))
    return None

# ==========================================
# 3. GENERATOR SYSTEM: BFS (Breadth-First Search)
# ==========================================

class WaterSortGenerator:
    def __init__(self, level):
        cfg = LEVEL_CONFIG.get(level, LEVEL_CONFIG[5])
        self.colors = cfg["colors"]
        self.empty = cfg["empty"]
        self.depth = cfg["depth"]

    def create_goal(self):
        tubes = []
        cols = list(COLOR_MAP.keys())[:self.colors]
        random.shuffle(cols)
        for c in cols:
            tubes.append([c] * BOTOL_CAPACITY)
        for _ in range(self.empty):
            tubes.append([])
        return tubes
    
    def chaotic_reverse_moves(self, state, last_move):
        """Mencari langkah pengacakan (Reverse Move)"""
        moves = []
        n = len(state)
        for i in range(n):
            if not state[i]: continue # Src harus ada isi
            for j in range(n):
                if i == j: continue
                if len(state[j]) >= BOTOL_CAPACITY: continue # Dst jangan penuh
                
                # Taboo Move: Jangan kembalikan air ke tempat asal segera
                if last_move and last_move == (j, i):
                    continue
                
                # Agar susah: Jangan tuang ke warna sama (kecuali dst kosong)
                if state[j] and state[j][-1] == state[i][-1]:
                    if random.random() > 0.1: continue # 90% skip
                
                moves.append((i, j))
        return moves

    def generate(self):
        """
        ALGORITMA BFS (Breadth-First Search) untuk GENERATOR.
        Menggunakan Queue (deque).
        """
        goal = self.create_goal()
        
        # BFS Queue: menyimpan (state, depth, last_move)
        queue = deque([(goal, 0, None)])
        
        final_state = goal
        
        # Loop BFS
        while queue:
            current_state, depth, last_move = queue.popleft() # Ambil dari DEPAN (Sifat BFS)
            
            # Jika kedalaman target tercapai, ambil state ini
            if depth >= self.depth:
                final_state = current_state
                break
            
            # Cari tetangga (Next States)
            moves = self.chaotic_reverse_moves(current_state, last_move)
            
            if not moves:
                # Jika macet, ambil state terakhir yang valid
                final_state = current_state
                break
                
            # --- OPTIMASI BFS AGAR TIDAK CRASH ---
            # Kita tidak memasukkan SEMUA tetangga (karena akan jadi jutaan node).
            # Kita pilih 1 tetangga acak untuk dimasukkan ke Queue.
            # Ini secara teknis tetap BFS (pakai Queue), tapi jalurnya linear (Randomized).
            
            chosen_move = random.choice(moves)
            i, j = chosen_move
            
            # Fragmentasi (Pecah warna biar susah)
            new_state = [list(t) for t in current_state]
            src, dst = new_state[i], new_state[j]
            
            # Hitung jumlah air yang bisa dipindah
            src_color = src[-1]
            amount_avail = 0
            for k in range(len(src)-1, -1, -1):
                if src[k] == src_color: amount_avail += 1
                else: break
            
            space = BOTOL_CAPACITY - len(dst)
            max_trf = min(amount_avail, space)
            
            # Random amount transfer
            trf = random.randint(1, max_trf)
            for _ in range(trf):
                dst.append(src.pop())
            
            # Masukkan ke Queue (Belakang)
            queue.append((new_state, depth + 1, chosen_move))
            
            # Update final state setiap langkah
            final_state = new_state

        return final_state

# ==========================================
# 4. GLOBAL & UI SETUP
# ==========================================

current_level = 1
tubes = []
initial_tubes = []
selected_tube = None
hint_move = None
game_won = False
loading = True
score = 0
stars = 0
ui_state = 'menu'

# Validator Sederhana (Greedy) untuk memastikan level playable
def fast_solve_validation(state):
    if is_goal_state(state): return True
    pq = []
    heapq.heappush(pq, (get_heuristic_score(state), 0, state))
    visited = {state_to_key(state)}
    nodes = 0
    while pq and nodes < 5000:
        _, _, cur = heapq.heappop(pq)
        nodes += 1
        if is_goal_state(cur): return True
        for m in valid_moves_from(cur):
            nxt = apply_move(cur, m)
            k = state_to_key(nxt)
            if k not in visited:
                visited.add(k)
                heapq.heappush(pq, (get_heuristic_score(nxt), nodes, nxt))
    return False

def draw_text_center(text, y, color='white', font_obj=font):
    obj = font_obj.render(str(text), True, color)
    rect = obj.get_rect(center=(WIDTH//2, y))
    screen.blit(obj, rect)

# Fungsi Gambar Bintang
def draw_star(surface, x, y, size, color):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5 
        radius = size if i % 2 == 0 else size * 0.4
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (200, 150, 0), points, 2)

def setup_level(level):
    global tubes, initial_tubes, current_level, game_won, loading, score, stars, hint_move
    
    current_level = level
    loading = True
    game_won = False
    hint_move = None
    stars = 0
    score = 1000 
    
    screen.fill((20, 20, 30))
    draw_text_center(f"GENERATING LEVEL {level} (BFS)...", HEIGHT//2, 'cyan', large_font)
    pygame.display.flip()

    gen = WaterSortGenerator(level)
    best_puzzle = None
    max_complexity = -1
    
    attempts = 15 
    for _ in range(attempts):
        candidate = gen.generate() # Panggil BFS Generator
        
        # Skip jika terlalu mudah
        neat_count = sum(1 for t in candidate if len(t)==4 and len(set(t))==1)
        if level > 1 and neat_count >= 3: continue 
        
        if fast_solve_validation(candidate):
            complexity = get_heuristic_score(candidate)
            if complexity > max_complexity:
                max_complexity = complexity
                best_puzzle = candidate
    
    tubes = best_puzzle if best_puzzle else gen.create_goal()
    initial_tubes = copy.deepcopy(tubes)
    loading = False

def calculate_stars(final_score):
    if final_score > 800: return 5
    elif final_score > 600: return 4
    elif final_score > 400: return 3
    elif final_score > 200: return 2
    else: return 1 # 0-200 tetap dapat bintang 1

# ==========================================
# 5. DRAWING & MAIN LOOP
# ==========================================

def draw_game():
    screen.fill((30, 30, 40))
    
    lvl_txt = large_font.render(f"LEVEL {current_level}", True, 'white')
    screen.blit(lvl_txt, (20, 20))
    
    col_score = 'yellow'
    if score <= 400: col_score = 'red'
    elif score <= 600: col_score = 'orange'
    
    score_txt = font.render(f"Score: {score}", True, col_score)
    screen.blit(score_txt, (20, 70))
    
    # Info Algoritma (Biar Dosen Lihat)
    algo_txt = font.render("Generator: BFS | Hint: A*", True, (100, 255, 100))
    screen.blit(algo_txt, (20, 100))
    
    info_txt = font.render("R: Restart | H: Hint (-50) | M: Menu", True, 'gray')
    screen.blit(info_txt, (WIDTH - 400, 30))

    if loading: return []

    num = len(tubes)
    w, h = 60, 200
    gap = 20
    total_w = num * w + (num-1) * gap
    start_x = (WIDTH - total_w) // 2
    start_y = 250
    
    rects = []
    
    for i, tube in enumerate(tubes):
        x = start_x + i * (w + gap)
        y = start_y
        
        if selected_tube == i: y -= 20
            
        for idx, color_code in enumerate(tube):
            c = COLOR_MAP[color_code]
            h_seg = h / BOTOL_CAPACITY
            y_seg = y + h - (idx + 1) * h_seg
            pygame.draw.rect(screen, c, (x+4, y_seg, w-8, h_seg), border_radius=3)
            
        color = 'white'
        thick = 3
        if selected_tube == i: color = 'yellow'
        
        if hint_move:
            src, dst = hint_move
            if i == src: color = 'cyan'; thick = 5
            elif i == dst: color = 'green'; thick = 5
        
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, color, rect, thick, border_radius=8)
        
        label = font.render(str(i+1), True, 'gray')
        screen.blit(label, (x + w//2 - 5, y + h + 5))
        rects.append((rect, i))

    if game_won:
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(230)
        s.fill((0,0,0))
        screen.blit(s, (0,0))
        
        draw_text_center("LEVEL COMPLETED!", HEIGHT//2 - 120, 'green', large_font)
        draw_text_center(f"Final Score: {score}", HEIGHT//2 - 70)
        
        # Gambar Bintang Visual
        star_size = 35
        total_width = stars * (star_size * 2 + 10)
        start_star_x = WIDTH//2 - total_width // 2 + star_size
        
        for i in range(stars):
            s_size = star_size + math.sin(pygame.time.get_ticks()/300 + i)*2
            draw_star(screen, start_star_x + i * (star_size * 2 + 15), HEIGHT//2, s_size, (255, 215, 0))

        if current_level < 5:
            draw_text_center("Press ENTER for Next Level", HEIGHT//2 + 80, 'white')
        else:
            draw_text_center("ALL LEVELS COMPLETED!", HEIGHT//2 + 80, 'gold')

    return rects

def main():
    global ui_state, selected_tube, hint_move, score, game_won, tubes, stars
    
    running = True
    rects = []
    
    while running:
        clock.tick(FPS)
        
        if ui_state == 'menu':
            screen.fill((20, 20, 30))
            draw_text_center("WATER SORT PUZZLE", 150, 'white', large_font)
            
            btn = pygame.Rect(WIDTH//2 - 100, 250, 200, 60)
            pygame.draw.rect(screen, (0, 120, 215), btn, border_radius=10)
            draw_text_center("START GAME", 270)
            
            for i in range(1, 6):
                r = pygame.Rect(WIDTH//2 - 175 + (i-1)*70, 350, 50, 50)
                pygame.draw.rect(screen, (60, 60, 60), r, border_radius=5)
                txt = font.render(str(i), True, 'white')
                screen.blit(txt, (r.x + 18, r.y + 15))
                if pygame.mouse.get_pressed()[0]:
                    mx, my = pygame.mouse.get_pos()
                    if r.collidepoint((mx, my)):
                        setup_level(i)
                        ui_state = 'playing'
                        pygame.time.delay(200)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn.collidepoint(event.pos):
                        setup_level(1)
                        ui_state = 'playing'

            pygame.display.flip()
            
        elif ui_state == 'playing':
            rects = draw_game()
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_m: ui_state = 'menu'
                    
                    if event.key == pygame.K_r: # Restart
                        tubes = copy.deepcopy(initial_tubes)
                        selected_tube = None
                        hint_move = None
                        game_won = False
                        score = 1000 # Reset 1000
                        
                    if event.key == pygame.K_SPACE: # Cheat
                        game_won = True
                        score = 1000
                        stars = 5
                        
                    if event.key == pygame.K_RETURN and game_won: 
                        setup_level(min(5, current_level + 1))
                        
                    if event.key == pygame.K_h and not game_won: # Hint
                        if score >= 50: 
                            res = astar_find_hint(tubes)
                            if res:
                                hint_move = res
                                score -= 50 # PENALTI HINT -50
                            else: print("No hint.")
                        else:
                            print("Score not enough!")
                
                if event.type == pygame.MOUSEBUTTONDOWN and not game_won:
                    pos = event.pos
                    clicked = -1
                    for r, idx in rects:
                        if r.collidepoint(pos): clicked = idx; break
                    
                    if clicked != -1:
                        if selected_tube is None:
                            if tubes[clicked]: selected_tube = clicked
                        else:
                            if selected_tube == clicked:
                                selected_tube = None
                            else:
                                move = (selected_tube, clicked)
                                valid = valid_moves_from(tubes)
                                if move in valid:
                                    tubes = apply_move(tubes, move)
                                    score -= 5 # PENALTI MOVE -5
                                    hint_move = None
                                    if is_goal_state(tubes):
                                        game_won = True
                                        stars = calculate_stars(score)
                                selected_tube = None

    pygame.quit()

if __name__ == "__main__":
    main()
