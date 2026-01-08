# main.py
import pygame
import sys

from config import *
from entities.player import Player
from entities.obstacle import Obstacle

# =========================
# LOAD IMAGES
# =========================
def load_images():
    sky = pygame.image.load("assets/background/sky.png").convert()
    ground = pygame.image.load("assets/background/ground.png").convert_alpha()
    return sky, ground

# =========================
# DRAW BACKGROUND
# =========================
def draw_background(screen, sky_img, ground_img, world_offset):
    """Draw sky and ground"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # Sky
    sky_scaled = pygame.transform.scale(sky_img, (screen_width, screen_height))
    screen.blit(sky_scaled, (0, 0))
    
    # Ground 
    ground_width = ground_img.get_width()
    ground_height = ground_img.get_height()
    y = screen_height - ground_height

    # Offset makes the ground scroll only when the user advances
    start_x = -(world_offset % ground_width)
    for x in range(start_x, screen_width, ground_img.get_width()):
        screen.blit(ground_img, (x, y))

# =========================
# MAIN GAME LOOP
# =========================
def main():
    # --- Init pygame ---
    pygame.init()
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # --- Load assets ---
    sky_img, ground_img = load_images()

    # --- Compute ground collision line ---
    screen_height = screen.get_height()
    ground_y = (screen_height- ground_img.get_height()+ GROUND_SURFACE_OFFSET)

    # --- Create player ---
    player = Player(x=80, ground_y=ground_y)
    
    # --- Create obstacles ---
    obstacles = [
    Obstacle(world_x=400, ground_y=ground_y, width=60, height=80),
    Obstacle(world_x=700, ground_y=ground_y, width=80, height=70),
    Obstacle(world_x=1000, ground_y=ground_y, width=60, height=60),
    ]

     # --- World state ---
    world_offset = 0  # how far the user progressed in the world
    MOVE_SPEED = 4    # speed when the user advances
    

    running = True
    while running:
        clock.tick(FPS)

        # =====================
        # Events
        # =====================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Jump 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()

        keys = pygame.key.get_pressed()
        

        # ==========================
        # UPDATE OBSTACLE POSITIONS
        # ==========================
        for obstacle in obstacles:
            obstacle.update_screen_position(world_offset)

        # ============================
        # GROUND / PLATFORM DETECTION
        # ============================
        # By default, the player is on the ground
        player_on_obstacle = False
        player.ground_y = ground_y  

        for obstacle in obstacles:
            # On vérifie si le joueur est posé sur l'obstacle
            # Compute reduced "feet" zone for stability
            foot_left = player.rect.left + FOOT_MARGIN
            foot_right = player.rect.right - FOOT_MARGIN

            # Horizontal overlap between feet and obstacle
            horizontal_ok = (
                foot_right > obstacle.rect.left and
                foot_left < obstacle.rect.right
            )
            # On vérifie si les pieds sont juste au-dessus de l'obstacle
            vertical_ok = (
                abs(player.rect.bottom - (obstacle.rect.top + PLAYER_FEET_OFFSET)) <= 5
            )
            
            # If both conditions are met, the player is on this obstacle
            if horizontal_ok and vertical_ok:
                player.ground_y = obstacle.rect.top + PLAYER_FEET_OFFSET
                player.velocity_y = 0
                player_on_obstacle = True
                break

        # ================================
        # HORIZONTAL COLLISION (BLOCKING)
        # ================================
        blocked = False
        if keys[pygame.K_RIGHT]:
            future_rect = player.rect.copy()
            future_rect.x += MOVE_SPEED

            for obstacle in obstacles:
                # If advancing would collide with an obstacle
                if future_rect.colliderect(obstacle.rect):
                    # l'obstacle doit être DEVANT le joueur
                    if obstacle.rect.left >= player.rect.right:
                        # Player is too low to climb onto it
                        if player.rect.bottom > obstacle.rect.top + 5 and not player_on_obstacle:
                            blocked = True
                            break  # On arrête dès qu'on trouve un blocage

        # =====================
        # WORLD MOVEMENT
        # =====================
        if keys[pygame.K_RIGHT] and not blocked:
            world_offset += MOVE_SPEED
            player.set_moving(True)
        else:
            player.set_moving(False)
        
     
        # =====================
        # PHYSICS UPDATE
        # =====================
        # Gravity + vertical movement + ground clamping
        player.update()

        
        # =====================
        # Draw
        # =====================
        draw_background(screen, sky_img, ground_img, world_offset)
        
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        player.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
