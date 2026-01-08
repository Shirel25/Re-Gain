import pygame
import sys

from config import TITLE
from game.game import Game
from input.input_manager import InputManager


# =========================
# LOAD IMAGES
# =========================
def load_images():
    sky = pygame.image.load("assets/background/sky.png").convert()
    ground = pygame.image.load("assets/background/ground.png").convert_alpha()
    return sky, ground


# =========================
# MAIN
# =========================
def main():
    # --- Init pygame ---
    pygame.init()
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h))
    pygame.display.set_caption(TITLE)

    # --- Load assets ---
    sky_img, ground_img = load_images()

    # --- Create game ---
    game = Game(screen, sky_img, ground_img)

    # --- Create input manager ---
    input_manager = InputManager(mode="keyboard")

    running = True
    while running:
        # =====================
        # Events
        # =====================
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # --- Update inputs ---
        input_manager.update(events)

        # --- Jump ---
        if input_manager.jump_pressed():
            game.player.jump()

        # =====================
        # Update & Draw
        # =====================
        game.update(input_manager)
        game.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
