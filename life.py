import argparse
import pygame
import random
import sys

# ---------------- Bootstrap ----------------
def get_args():
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument("--width", type=int, default=40, help="Grid width")
    parser.add_argument("--height", type=int, default=20, help="Grid height")
    parser.add_argument("--fps", type=int, default=6, help="Frames per second")
    return parser.parse_args()


# ---------------- Model ----------------
def make_board(width, height):
    return [[0 for _ in range(width)] for _ in range(height)]


def count_neighbors(board, x, y):
    H, W = len(board), len(board[0])
    total = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = (x + dx) % H, (y + dy) % W
            total += board[nx][ny]
    return total


def next_gen(board):
    H, W = len(board), len(board[0])
    new_board = make_board(W, H)
    for i in range(H):
        for j in range(W):
            neighbors = count_neighbors(board, i, j)
            if board[i][j] == 1 and neighbors in (2, 3):
                new_board[i][j] = 1
            elif board[i][j] == 0 and neighbors == 3:
                new_board[i][j] = 1
    return new_board


# ---------------- Persistence ----------------
def save_pattern(board, filename):
    with open(filename, "w") as f:
        f.write("# Pattern: Saved\n")
        for i, row in enumerate(board):
            for j, cell in enumerate(row):
                if cell == 1:
                    f.write(f"{i},{j}\n")


def load_patterns(filename):
    patterns = {}
    current_name, coords = None, []
    try:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("# Pattern:"):
                    if current_name and coords:
                        patterns[current_name] = coords
                    current_name = line.split(":", 1)[1].strip()
                    coords = []
                else:
                    try:
                        i, j = map(int, line.split(","))
                        coords.append((i, j))
                    except ValueError:
                        pass
            if current_name and coords:
                patterns[current_name] = coords
    except FileNotFoundError:
        return {}
    return patterns


def apply_pattern(board, coords):
    H, W = len(board), len(board[0])
    new_board = make_board(W, H)
    for i, j in coords:
        if 0 <= i < H and 0 <= j < W:
            new_board[i][j] = 1
    return new_board


# ---------------- View ----------------
def draw_board(screen, board, cell_size):
    screen.fill((0, 0, 0))
    H, W = len(board), len(board[0])
    live_count = 0

    for i in range(H):
        for j in range(W):
            if board[i][j] == 1:
                live_count += 1
                pygame.draw.rect(
                    screen, (0, 255, 0),
                    (j*cell_size, i*cell_size, cell_size-1, cell_size-1)
                )
    return live_count


def draw_hud(screen, gen, live_count, running, fps, W, H, cell_size):
    font = pygame.font.SysFont("Consolas", 18)
    status = "▶" if running else "⏸"

    hud_lines = [
        "┌ Game of Life ──────────────────────────────┐",
        f"│ Space:{status}  N:Step  R:Random  S:Save  L:Load│",
        f"│ Generation {gen:<5}   Live cells: {live_count:<5}   FPS: {fps:<2} │",
        "└─────────────────────────────────────────────┘",
    ]

    pygame.draw.rect(screen, (0, 0, 0), (0, H*cell_size, W*cell_size, 80))
    for i, line in enumerate(hud_lines):
        text = font.render(line, True, (0, 255, 255))
        screen.blit(text, (10, H*cell_size + i*20))

    pygame.display.flip()


# ---------------- Main Loop ----------------
def main():
    args = get_args()
    W, H, FPS = args.width, args.height, args.fps
    CELL_SIZE = 20
    WIDTH, HEIGHT = W*CELL_SIZE, H*CELL_SIZE + 80

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Conway's Game of Life")
    clock = pygame.time.Clock()

    board = make_board(W, H)
    running = False
    generation = 0

    patterns = load_patterns("patterns.txt")
    pattern_keys = {
        pygame.K_1: "Glider",
        pygame.K_2: "Blinker",
        pygame.K_3: "Toad",
        pygame.K_4: "Pulsar",
        pygame.K_5: "Lightweight Spaceship (LWSS)",
    }

    while True:
        live_count = draw_board(screen, board, CELL_SIZE)
        draw_hud(screen, generation, live_count, running, FPS, W, H, CELL_SIZE)
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Play/Pause
                    running = not running
                elif event.key == pygame.K_n:  # Step once
                    board = next_gen(board)
                    generation += 1
                    running = False
                elif event.key == pygame.K_c:  # Clear
                    board = make_board(W, H)
                    generation = 0
                elif event.key == pygame.K_r:  # Random fill
                    for i in range(H):
                        for j in range(W):
                            board[i][j] = random.choice([0, 1])
                    generation = 0
                elif event.key == pygame.K_s:  # Save
                    save_pattern(board, "saved.txt")
                    print("Saved current pattern to saved.txt")
                elif event.key == pygame.K_l:  # Load saved
                    saved = load_patterns("saved.txt")
                    if saved:
                        name, coords = next(iter(saved.items()))
                        board = apply_pattern(make_board(W, H), coords)
                        generation = 0
                        print(f"Loaded saved pattern: {name}")
                elif event.key in pattern_keys:  # Load from library
                    name = pattern_keys[event.key]
                    if name in patterns:
                        board = apply_pattern(make_board(W, H), patterns[name])
                        generation = 0
                        print(f"Loaded pattern: {name}")

            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if my < H*CELL_SIZE:
                    j, i = mx // CELL_SIZE, my // CELL_SIZE
                    board[i][j] = 1

        if running:
            board = next_gen(board)
            generation += 1


if __name__ == "__main__":
    main()
