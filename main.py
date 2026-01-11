import pygame
import sys

from config import TITLE
from game.game import Game
from input.input_manager import InputManager
from calibration.calibration import fake_calibration


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

    # --- Calibration (fake for now) ---
    calibration = fake_calibration()

    # --- Create input manager ---
    input_manager = InputManager(mode="fake_emg", calibration=calibration)

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

        if game.session_finished:
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                if game.session_finished and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        mouse_pos = pygame.mouse.get_pos()

                        if game.restart_button_rect and game.restart_button_rect.collidepoint(mouse_pos):
                            main()   # relance une nouvelle session
                            return

                        if game.quit_button_rect and game.quit_button_rect.collidepoint(mouse_pos):
                            running = False


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
