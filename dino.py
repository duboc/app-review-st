import pygame
import random

pygame.init()

# Window settings
WIDTH = 1200
HEIGHT = 800
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Dino settings
DINO_X = 100
DINO_Y = HEIGHT - 100
DINO_WIDTH = 40
DINO_HEIGHT = 60
JUMP_HEIGHT = 15
GRAVITY = 0.8
is_jumping = False
dino_y_velocity = 0

# Obstacle settings
OBSTACLE_WIDTH = 30
OBSTACLE_MIN_HEIGHT = 40
OBSTACLE_MAX_HEIGHT = 150
OBSTACLE_SPEED = 8
obstacles = []

# Score
score = 0
font = pygame.font.Font(None, 36)

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()

# --- Functions ---
def reset_game():
    """Resets game variables to their initial state."""
    global score, obstacles, DINO_Y, is_jumping, dino_y_velocity
    score = 0
    obstacles = []
    DINO_Y = HEIGHT - DINO_HEIGHT
    is_jumping = False
    dino_y_velocity = 0

def show_game_over():
    """Displays the game over message and restart button."""
    game_over_text = font.render("Game Over", True, BLACK)
    restart_text = font.render("Press 'R' to Restart", True, BLACK)
    screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
    screen.blit(restart_text, (WIDTH // 2 - 130, HEIGHT // 2 + 50))
    pygame.display.flip()

# --- Game loop ---
running = True
game_over = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_jumping:
                is_jumping = True
                dino_y_velocity = -JUMP_HEIGHT
            if event.key == pygame.K_r and game_over:
                game_over = False
                reset_game()

    if not game_over:
        # Dino jump
        if is_jumping:
            dino_y_velocity += GRAVITY
            DINO_Y += dino_y_velocity
            if DINO_Y >= HEIGHT - DINO_HEIGHT:
                DINO_Y = HEIGHT - DINO_HEIGHT
                is_jumping = False  # Reset is_jumping when dino lands

        # Generate obstacles
        if len(obstacles) == 0 or obstacles[-1][0] < WIDTH - 400:
            obstacle_height = random.randint(OBSTACLE_MIN_HEIGHT, OBSTACLE_MAX_HEIGHT)
            obstacles.append([WIDTH, HEIGHT - obstacle_height, OBSTACLE_WIDTH, obstacle_height])

        # Move and remove obstacles
        for obstacle in obstacles:
            obstacle[0] -= OBSTACLE_SPEED
            if obstacle[0] < -OBSTACLE_WIDTH:
                obstacles.pop(0)
                score += 1

        # Collision detection
        dino_rect = pygame.Rect(DINO_X, DINO_Y, DINO_WIDTH, DINO_HEIGHT)
        for obstacle in obstacles:
            obstacle_rect = pygame.Rect(obstacle)
            if dino_rect.colliderect(obstacle_rect):
                game_over = True  # Trigger game over state

        # Render
        screen.fill(WHITE)

        # Draw dino
        pygame.draw.rect(screen, BLACK, (DINO_X, DINO_Y, DINO_WIDTH, DINO_HEIGHT))

        # Draw obstacles
        for obstacle in obstacles:
            pygame.draw.rect(screen, BLACK, obstacle)

        # Draw score
        score_text = font.render("Score: " + str(score), True, BLACK)
        screen.blit(score_text, (10, 10))

        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    else:
        show_game_over()

pygame.quit()
