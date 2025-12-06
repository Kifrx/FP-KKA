import pygame
import random
import copy
import time
from collections import deque
import heapq

# --- INISIALISASI PYGAME ---
pygame.init()

WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Water Sort Puzzle - Final BFS Project (with HINT)')
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
        if not src_tube:
            return 0

        color_src = src_tube[-1]

        # Kasus 1: Nuang ke botol kosong
        if not dst_tube:
            # Di level tinggi, nuang ke kosong itu 'kurang chaos' (skor sedang)
            return 5 if self.level < 3 else 1

        color_dst = dst_tube[-1]

        # Kasus 2: Nuang ke warna BEDA (CHAOS!)
        if color_src != color_dst:
            return 10  # Prioritas TERTINGGI

        return 0

    def generate_with_bfs(self):
        """
        Algoritma: Randomized Reverse BFS
        """
        goal_state = self.create_goal_state()

        queue = deque([(goal_state, 0, None)])

        final_state = goal_state
        visited_count = 0
        max_visit = 5000  # Safety break

        print(f"BFS Generating Level {self.level} (Target Depth: {self.target_depth})...")

        while queue:
            current_state, depth, last_move = queue.popleft()
            visited_count += 1

            if depth > 0:
                final_state = current_state

            if depth >= self.target_depth or visited_count > max_visit:
                return current_state

            # --- EXPAND NODE (Cari Anak) ---
            potential_moves = []

            for i in range(len(current_state)):
                for j in range(len(current_state)):
                    if i == j:
                        continue

                    src, dst = current_state[i], current_state[j]

                    # Syarat Valid Reverse
                    if len(src) > 0 and len(dst) < BOTOL_CAPACITY:
                        if last_move and last_move == (j, i):
                            continue

                        # Hitung Skor Chaos
                        score = self.get_chaos_score(src, dst)

                        # PRUNING: Hanya ambil gerakan yang punya skor chaos > 0
                        if score > 0:
                            potential_moves.append((score, i, j))

            # Kalau tidak ada gerakan chaos, cari gerakan apa saja
            if not potential_moves:
                for i in range(len(current_state)):
                    for j in range(len(current_state)):
                        if i == j:
                            continue
                        if len(current_state[i]) > 0 and len(current_state[j]) < BOTOL_CAPACITY:
                            if last_move and last_move == (j, i):
                                continue
                            potential_moves.append((1, i, j))

            if not potential_moves:
                continue

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
hint_move = None  # (src_idx, dst_idx) for visual hint
game_won = False
loading = True

# Star & hint usage
hint_used = 0
stars = 0

# ---------- A* HINT FUNCTIONS ----------

def state_to_key(state):
    return tuple(tuple(t) for t in state)


def is_goal_state(state):
    for tube in state:
        if len(tube) == 0:
            continue
        if len(tube) < BOTOL_CAPACITY:
            return False
        first = tube[0]
        for c in tube:
            if c != first:
                return False
    return True


def heuristic(state):
    """
    Heuristic sederhana: jumlah transisi warna di tiap tabung.
    Semakin kecil, semakin 'rapi'.
    """
    h = 0
    for tube in state:
        if not tube:
            continue
        for i in range(len(tube) - 1):
            if tube[i] != tube[i + 1]:
                h += 1
        # if tube not full, penalize a bit (we want full same-colored tubes)
        if len(tube) < BOTOL_CAPACITY:
            h += (BOTOL_CAPACITY - len(tube))
    return h


def valid_moves_from(state):
    moves = []
    n = len(state)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            src = state[i]
            dst = state[j]
            if len(src) == 0 or len(dst) >= BOTOL_CAPACITY:
                continue
            src_color = src[-1]
            if len(dst) > 0 and dst[-1] != src_color:
                continue
            moves.append((i, j))
    return moves


def apply_move(state, move):
    i, j = move
    new_state = [list(t) for t in state]
    if len(new_state[i]) == 0:
        return None
    src_color = new_state[i][-1]
    amount = 0
    for k in range(len(new_state[i]) - 1, -1, -1):
        if new_state[i][k] == src_color:
            amount += 1
        else:
            break
    space = BOTOL_CAPACITY - len(new_state[j])
    final_amount = min(amount, space)
    for _ in range(final_amount):
        new_state[j].append(new_state[i].pop())
    return new_state



def astar_find_hint(start_state, time_limit=0.8, max_nodes=20000):
    """
    A* search that returns the first move of the best path found within limits.
    If no path to goal found within limits, returns None and caller will fallback.
    """
    start_key = state_to_key(start_state)
    if is_goal_state(start_state):
        return None

    t0 = time.time()

    open_heap = []
    # heap items: (f, g, key, state, parent_key, move_from_parent)
    h0 = heuristic(start_state)
    heapq.heappush(open_heap, (h0, 0, start_key, start_state, None, None))

    came_from = {}
    g_score = {start_key: 0}

    nodes = 0

    while open_heap:
        if time.time() - t0 > time_limit:
            break
        f, g, key, state, parent_key, move = heapq.heappop(open_heap)
        nodes += 1
        if nodes > max_nodes:
            break

        if key in came_from:  # we've already processed a better path
            continue

        came_from[key] = (parent_key, move)

        if is_goal_state(state):
            # reconstruct path
            path_moves = []
            cur = key
            while came_from[cur][0] is not None:
                pk, mv = came_from[cur]
                path_moves.append(mv)
                cur = pk
            path_moves.reverse()
            if path_moves:
                return path_moves[0]
            else:
                return None

        for mv in valid_moves_from(state):
            new_state = apply_move(state, mv)
            if new_state is None:
                continue
            nk = state_to_key(new_state)
            tentative_g = g + 1
            if tentative_g < g_score.get(nk, float('inf')):
                g_score[nk] = tentative_g
                h = heuristic(new_state)
                heapq.heappush(open_heap, (tentative_g + h, tentative_g, nk, new_state, key, mv))

    # if search didn't find solution, attempt to pick the best immediate move (greedy by heuristic)
    best = None
    best_h = float('inf')
    for mv in valid_moves_from(start_state):
        s = apply_move(start_state, mv)
        if s is None:
            continue
        h = heuristic(s)
        if h < best_h:
            best_h = h
            best = mv
    return best


# ==========================================
# UI & GAME FUNCTIONS
# ==========================================

def setup_level(level):
    global tubes, initial_tubes, game_won, loading, hint_move, hint_used, stars
    loading = True
    draw_loading(level)
    hint_move = None
    hint_used = 0
    stars = 0
    # GENERATOR BERAKSI
    gen = WaterSortGenerator(level)
    tubes = gen.generate_with_bfs()

    initial_tubes = copy.deepcopy(tubes)
    game_won = False
    loading = False


def draw_loading(level):
    screen.fill((20, 20, 20))
    text = font.render(f'GENERATING LEVEL {level}... (Please Wait)', True, 'white')
    screen.blit(text, (WIDTH // 2 - 180, HEIGHT // 2))
    pygame.display.flip()

def draw_game_interface():
    global hint_move, selected_tube, stars
    screen.fill((30, 30, 30))

    # Header
    level_text = font.render(f'LEVEL: {current_level}', True, 'white')
    screen.blit(level_text, (20, 20))
    hint_text = font.render('R: Restart | SPACE: Skip Level (Cheat) | H: Hint (A*)', True, 'gray')
    screen.blit(hint_text, (WIDTH - 520, 20))

    if loading:
        return []

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
            border_color = (255, 255, 0)  # Kuning
            thickness = 5
            y -= 20

        # If this tube is part of hint, highlight differently
        if hint_move is not None:
            try:
                src_idx, dst_idx = hint_move
                if i == src_idx:
                    border_color = (0, 255, 255)  # Cyan for source hint
                    thickness = 6
                    y -= 10
                if i == dst_idx:
                    border_color = (0, 200, 0)    # Green for destination hint
                    thickness = 6
            except Exception:
                # if hint_move malformed, ignore
                pass

        # 1. Gambar Air
        for idx, color_code in enumerate(tubes[i]):
            color = COLOR_MAP.get(color_code, (255, 255, 255))
            h_unit = tube_height / BOTOL_CAPACITY
            # Koordinat Y air (dari bawah ke atas)
            water_y = (y + tube_height) - ((idx + 1) * h_unit)

            # Sedikit padding biar air ada di dalam garis tabung
            pygame.draw.rect(screen, color, [int(x + 5), int(water_y), int(tube_width - 10), int(h_unit)], 0, 8)

        # 2. Gambar Tabung
        tube_rect = pygame.Rect(int(x), int(y), tube_width, tube_height)
        pygame.draw.rect(screen, border_color, tube_rect, thickness, 8)
        rects.append(tube_rect)

    if game_won:
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(150)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))

        msg = large_font.render('LEVEL COMPLETED!', True, (0, 255, 0))
        sub_msg = font.render('Press ENTER for Next Level', True, 'white')
        screen.blit(msg, (WIDTH // 2 - 180, HEIGHT // 2 - 50))
        screen.blit(sub_msg, (WIDTH // 2 - 140, HEIGHT // 2 + 10))

        # draw stars if available (manual polygon drawing)
        if stars > 0:
            def draw_star(surface, x, y, size, color):
                # approximate 5-point star polygon; convert coords to int
                pts = [
                    (int(x), int(y - size)),
                    (int(x + size * 0.2245), int(y - size * 0.3090)),
                    (int(x + size), int(y - size * 0.3090)),
                    (int(x + size * 0.3633), int(y + size * 0.1180)),
                    (int(x + size * 0.5878), int(y + size)),
                    (int(x), int(y + size * 0.3819)),
                    (int(x - size * 0.5878), int(y + size)),
                    (int(x - size * 0.3633), int(y + size * 0.1180)),
                    (int(x - size), int(y - size * 0.3090)),
                    (int(x - size * 0.2245), int(y - size * 0.3090))
                ]
                pygame.draw.polygon(surface, color, pts)

            # center the stars above the message
            total_width = (stars - 1) * 60
            start_x_stars = (WIDTH // 2) - (total_width // 2) - 30 * (stars - 1)
            for s_idx in range(stars):
                draw_star(screen, WIDTH // 2 - 60 + s_idx * 60, HEIGHT // 2 - 100, 30, (255, 215, 0))

    return rects



def check_victory():
    for tube in tubes:
        if len(tube) == 0:
            continue
        if len(tube) < BOTOL_CAPACITY:
            return False
        first = tube[0]
        for c in tube:
            if c != first:
                return False
    return True


def handle_move(src_idx, dst_idx):
    global tubes
    src = tubes[src_idx]
    dst = tubes[dst_idx]

    if len(src) == 0:
        return
    if len(dst) >= BOTOL_CAPACITY:
        return

    src_color = src[-1]
    if len(dst) > 0 and dst[-1] != src_color:
        return

    # Pindahkan semua blok warna yang sama (Stack logic)
    amount_to_move = 0
    for i in range(len(src) - 1, -1, -1):
        if src[i] == src_color:
            amount_to_move += 1
        else:
            break

    space = BOTOL_CAPACITY - len(dst)
    final_amount = min(amount_to_move, space)

    for _ in range(final_amount):
        dst.append(src.pop())


# ==========================================
# 3. MAIN LOOP
# ==========================================

def main():
    global current_level, selected_tube, tubes, game_won, hint_move, hint_used, stars

    run = True
    setup_level(current_level)

    while run:
        timer.tick(FPS)
        tube_rects = draw_game_interface()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r:  # Restart
                    tubes = copy.deepcopy(initial_tubes)
                    selected_tube = None
                    game_won = False
                    hint_move = None
                    hint_used = 0
                    stars = 0

                if event.key == pygame.K_SPACE:  # Cheat
                    game_won = True

                if event.key == pygame.K_RETURN and game_won:  # Next Level
                    if current_level < 5:
                        current_level += 1
                        setup_level(current_level)
                    else:
                        print("TAMAT!")
                        current_level = 1
                        setup_level(current_level)

                if event.key == pygame.K_h and not game_won and not loading:
                    # Compute 1-step hint using A*
                    hint_used += 1
                    hint_move = astar_find_hint(tubes)
                    if hint_move is None:
                        print("Hint: tidak ditemukan atau sudah rapi")
                    else:
                        print(f"Hint: tuang dari {hint_move[0]} ke {hint_move[1]}")

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
                            hint_move = None
                            # cek victory dan set stars
                            if check_victory():
                                game_won = True
                                if hint_used == 0:
                                    stars = 3
                                elif hint_used <= 3:
                                    stars = 2
                                else:
                                    stars = 1
                                print(f"Level complete dengan {stars} bintang!")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
