import pygame
import random
import copy
import time
from collections import deque

# --- INISIALISASI PYGAME ---
pygame.init()

WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Water Sort Puzzle - Final BFS Project')
font = pygame.font.Font('freesansbold.ttf', 20)
large_font = pygame.font.Font('freesansbold.ttf', 40)
timer = pygame.time.Clock()
FPS = 60

# --- WARNA RGB ---
COLOR_MAP = {
    1: (220, 20, 60),    # Crimson (Merah)
    2: (65, 105, 225),   # Royal Blue (Biru)
    3: (50, 205, 50),    # Lime Green (Hijau)
    4: (255, 215, 0),    # Gold (Kuning)
    5: (138, 43, 226),   # Blue Violet (Ungu)
    6: (255, 140, 0),    # Dark Orange
    7: (0, 255, 255),    # Cyan
    8: (255, 105, 180),  # Hot Pink
    9: (169, 169, 169)   # Dark Gray
}


BOTOL_CAPACITY = 4
LEVEL_CONFIG = {
    1: {"colors": 3, "empty": 2, "depth": 12},  
    2: {"colors": 4, "empty": 2, "depth": 25},   
    3: {"colors": 5, "empty": 2, "depth": 40},   
    4: {"colors": 6, "empty": 2, "depth": 55},  
    5: {"colors": 7, "empty": 2, "depth": 70}    
}

# ==========================================
# CLASS GENERATOR: REVERSE BFS WITH CHAOS PRUNING
# ==========================================
class WaterSortGenerator:
    def __init__(self, level):
        config = LEVEL_CONFIG.get(level, LEVEL_CONFIG[5])
        self.level = level
        self.num_colors = config["colors"]
        self.num_empty = config["empty"]
        
        self.target_depth = config["depth"] + 10 

    def create_goal_state(self):
        """Buat Botol Rapi (Goal)"""
        bottles = []
        available_colors = list(COLOR_MAP.keys())[:self.num_colors]
        random.shuffle(available_colors) 
        
        for color in available_colors:
            bottles.append([color] * BOTOL_CAPACITY)
        for _ in range(self.num_empty):
            bottles.append([])
        return bottles

    def get_chaos_score(self, src_tube, dst_tube):
        """
        Memberi Nilai 'Kekacauan'.
        High Score = Bagus (Warna beda/berantakan).
        Low Score = Jelek (Warna sama/numpuk rapi).
        """
        if not src_tube: return 0
        
        color_src = src_tube[-1]
        
        # Kasus 1: Nuang ke botol kosong
        if not dst_tube:
            # Di level tinggi, nuang ke kosong itu 'kurang chaos' (skor sedang)
            return 5 if self.level < 3 else 1
            
        color_dst = dst_tube[-1]
        
        # Kasus 2: Nuang ke warna BEDA (CHAOS!)
        if color_src != color_dst:
            return 10 # Prioritas TERTINGGI
            
        return 0 

    def generate_with_bfs(self):
        """
        Algoritma: Randomized Reverse BFS
        """
        goal_state = self.create_goal_state()
        
        # BFS
   
        queue = deque([ (goal_state, 0, None) ])
        
        final_state = goal_state
        visited_count = 0
        max_visit = 5000 # Safety break
        
        print(f"BFS Generating Level {self.level} (Target Depth: {self.target_depth})...")

        while queue:
            current_state, depth, last_move = queue.popleft() 
            visited_count += 1
            
    
            if depth > 0: final_state = current_state

            if depth >= self.target_depth or visited_count > max_visit:
                return current_state

            # --- EXPAND NODE (Cari Anak) ---
            potential_moves = []
            
            for i in range(len(current_state)):
                for j in range(len(current_state)):
                    if i == j: continue
                    
                    src, dst = current_state[i], current_state[j]
                    
                    # Syarat Valid Reverse
                    if len(src) > 0 and len(dst) < BOTOL_CAPACITY:
                        if last_move and last_move == (j, i): continue
                        
                        # Hitung Skor Chaos
                        score = self.get_chaos_score(src, dst)
                        
                        # PRUNING: Hanya ambil gerakan yang punya skor chaos > 0
                        if score > 0:
                            potential_moves.append((score, i, j))

            # Kalau tidak ada gerakan chaos, cari gerakan apa saja 
            if not potential_moves:
                 for i in range(len(current_state)):
                    for j in range(len(current_state)):
                        if i == j: continue
                        if len(current_state[i]) > 0 and len(current_state[j]) < BOTOL_CAPACITY:
                             if last_move and last_move == (j, i): continue
                             potential_moves.append((1, i, j))

            if not potential_moves: continue

            
            # Acak sedikit biar gak deterministik
            random.shuffle(potential_moves) 
            
            # Urutkan berdasarkan skor chaos tertinggi
            potential_moves.sort(key=lambda x: x[0], reverse=True)
            
            # Ambil 1 langkah terbaik (Greedy-BFS)
            best_move = potential_moves[0] 
            score, src_idx, dst_idx = best_move
            
            # Eksekusi State Baru
            new_state = copy.deepcopy(current_state)
            water = new_state[src_idx].pop()
            new_state[dst_idx].append(water)
            
            # Masukkan ke Queue Belakang
            queue.append((new_state, depth + 1, (src_idx, dst_idx)))
            
        return final_state
# ==========================================
# 2. LOGIKA GAMEPLAY & VISUALISASI
# ==========================================

current_level = 1
tubes = []             
initial_tubes = []     
selected_tube = None   
game_won = False
loading = True

def setup_level(level):
    global tubes, initial_tubes, game_won, loading
    loading = True
    draw_loading(level) 
    
    # GENERATOR BERAKSI
    gen = WaterSortGenerator(level)
    tubes = gen.generate_with_bfs()
    
    initial_tubes = copy.deepcopy(tubes)
    game_won = False
    loading = False

def draw_loading(level):
    screen.fill((20, 20, 20))
    text = font.render(f'GENERATING LEVEL {level}... (Please Wait)', True, 'white')
    screen.blit(text, (WIDTH//2 - 180, HEIGHT//2))
    pygame.display.flip()

def draw_game_interface():
    screen.fill((30, 30, 30)) 
    
    # Header
    level_text = font.render(f'LEVEL: {current_level}', True, 'white')
    screen.blit(level_text, (20, 20))
    hint_text = font.render('R: Restart | SPACE: Skip Level (Cheat)', True, 'gray')
    screen.blit(hint_text, (WIDTH - 420, 20))

    if loading: return []

    num_tubes = len(tubes)
    tube_width = 70
    tube_height = 250
    gap = 25
    
    # Auto center posisi tabung
    total_width = (num_tubes * tube_width) + ((num_tubes - 1) * gap)
    start_x = (WIDTH - total_width) // 2
    start_y = 200

    rects = [] 

    for i in range(num_tubes):
        x = start_x + (i * (tube_width + gap))
        y = start_y
        
        # Highlight Pilihan
        border_color = (200, 200, 200)
        thickness = 3
        if selected_tube == i:
            border_color = (255, 255, 0) # Kuning
            thickness = 5
            y -= 20 

        # 1. Gambar Air
        for idx, color_code in enumerate(tubes[i]):
            color = COLOR_MAP[color_code]
            h_unit = tube_height / BOTOL_CAPACITY
            # Koordinat Y air (dari bawah ke atas)
            water_y = (y + tube_height) - ((idx + 1) * h_unit)
            
            # Sedikit padding biar air ada di dalam garis tabung
            pygame.draw.rect(screen, color, [x + 5, water_y, tube_width - 10, h_unit], 0, 8)

        # 2. Gambar Tabung
        tube_rect = pygame.Rect(x, y, tube_width, tube_height)
        pygame.draw.rect(screen, border_color, tube_rect, thickness, 8)
        rects.append(tube_rect)

    if game_won:
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(150)
        s.fill((0,0,0))
        screen.blit(s, (0,0))
        
        msg = large_font.render('LEVEL COMPLETED!', True, (0, 255, 0))
        sub_msg = font.render('Press ENTER for Next Level', True, 'white')
        screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
        screen.blit(sub_msg, (WIDTH//2 - 140, HEIGHT//2 + 10))

    return rects

def check_victory():
    for tube in tubes:
        if len(tube) == 0: continue 
        if len(tube) < BOTOL_CAPACITY: return False 
        first = tube[0]
        for c in tube:
            if c != first: return False
    return True

def handle_move(src_idx, dst_idx):
    src = tubes[src_idx]
    dst = tubes[dst_idx]

    if len(src) == 0: return 
    if len(dst) >= BOTOL_CAPACITY: return 

    src_color = src[-1] 
    if len(dst) > 0 and dst[-1] != src_color: return 

    # Pindahkan semua blok warna yang sama (Stack logic)
    amount_to_move = 0
    for i in range(len(src)-1, -1, -1):
        if src[i] == src_color: amount_to_move += 1
        else: break
    
    space = BOTOL_CAPACITY - len(dst)
    final_amount = min(amount_to_move, space)

    for _ in range(final_amount):
        dst.append(src.pop())

# ==========================================
# 3. MAIN LOOP
# ==========================================
def main():
    global current_level, selected_tube, tubes, game_won

    run = True
    setup_level(current_level)

    while run:
        timer.tick(FPS)
        tube_rects = draw_game_interface()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r: # Restart
                    tubes = copy.deepcopy(initial_tubes)
                    selected_tube = None
                    game_won = False
                
                if event.key == pygame.K_SPACE: # Cheat
                    game_won = True
                
                if event.key == pygame.K_RETURN and game_won: # Next Level
                    if current_level < 5:
                        current_level += 1
                        setup_level(current_level)
                    else:
                        print("TAMAT!")
                        current_level = 1 
                        setup_level(current_level)

            if event.type == pygame.MOUSEBUTTONDOWN and not game_won:
                pos = event.pos
                clicked_idx = -1
                for i, rect in enumerate(tube_rects):
                    if rect.collidepoint(pos):
                        clicked_idx = i
                        break
                
                if clicked_idx != -1:
                    if selected_tube is None:
                        if len(tubes[clicked_idx]) > 0:
                            selected_tube = clicked_idx
                    else:
                        if selected_tube == clicked_idx:
                            selected_tube = None
                        else:
                            handle_move(selected_tube, clicked_idx)
                            selected_tube = None
                            if check_victory(): game_won = True

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()