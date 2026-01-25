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
    calibration = fake_calibration()
    device = None
    print("\nFake calibration utilisée. Lancement du jeu...")
    time.sleep(1)

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
    input_manager = InputManager(mode="fake_emg", calibration=calibration, device=device)
    input_manager.start_session(session_index=1, fresh=True)   # UPDATED; first session, no fatigue

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

        # # --- Jump --- # 
        if input_manager.jump_pressed():
            game.player.jump()

        # =====================
        # Update & Draw
        # =====================
        game.update(input_manager)
        game.draw(input_manager)

        pygame.display.flip()

        if game.session_finished:
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()

                    # UPDATED; fatigue resume button
                    if game.fatigued and game.fatigue_resume_button_rect and game.fatigue_resume_button_rect.collidepoint(mouse_pos):
                        game.fatigued = False
                        input_manager.reset_fatigue_after_rest()

                    # --- end-session buttons ---
                    if game.session_finished:
                    
                        if game.restart_button_rect and game.restart_button_rect.collidepoint(mouse_pos):
                            main()   # relance une nouvelle session
                            return

                        if game.quit_button_rect and game.quit_button_rect.collidepoint(mouse_pos):
                            running = False
                            
                        if game.continue_button_rect and game.continue_button_rect.collidepoint(mouse_pos):
                            game.continue_session(input_manager) #UPDATED; continue the session
                            




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
