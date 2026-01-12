import pygame
import sys
import time

from bitalino import BITalino
from config import TITLE, MAC_ADDRESS
from game.game import Game
from input.input_manager import InputManager
from calibration.calibration import fake_calibration
from calibration.real_calibration import real_calibration
from input.emg import DualEMGInput

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
    # --- Calibration ---
    calibration = real_calibration()
    print("\nCalibration terminée. Lancement du jeu...")
    time.sleep(1)

    # --- Device ---
    device = BITalino(MAC_ADDRESS)
    device.start(1000, [5, 2])  # ARM + LEG # A5 est le premier canal analogique -> Colonne 5
                                            # A2 est le deuxième canal analogique -> Colonne 6

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
    input_manager = InputManager(mode="dual_emg", calibration=calibration, device=device)

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


        # ==== Test ====
        if isinstance(input_manager.input, DualEMGInput):
            print(
                f"ARM={input_manager.input.arm_activation:.2f} | "
                f"LEG={input_manager.input.leg_activation:.2f}",
                end="\r"
            )

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
