# ================================================================
# GAME LOOP
# - BOUCLE COURTE (loop 1): adaptation en temps réel
#   -> interprétation du signal EMG
#   -> vitesse de déplacement discrète (lente, normale, rapide)
#
# - BOUCLE LONGUE (loop 2): adaptation progressive de la difficulté
#   -> apparition d'obstacles plus ou moins fréquente
# ================================================================

import pygame
import random
import time

from config import FPS, GROUND_SURFACE_OFFSET, FOOT_MARGIN, PLAYER_FEET_OFFSET
from entities.player import Player
from entities.obstacle import Obstacle
from input.input_manager import InputManager
from entities.flag import Flag


# ===========================================
# BOUCLE COURTE
# Discrete speed levels adapted in real time
# ===========================================

SPEED_SLOW = 2.0
SPEED_NORMAL = 4.0
SPEED_FAST = 6.0


class Game:
    def __init__(self, screen, sky_img, ground_img):
        self.screen = screen
        self.clock = pygame.time.Clock()

        # Assets
        self.sky_img = sky_img
        self.ground_img = ground_img

        # World
        self.world_offset = 0
        self.move_speed = 4
    

        # Ground
        screen_height = self.screen.get_height()
        self.ground_y = (
            screen_height - self.ground_img.get_height() + GROUND_SURFACE_OFFSET
        )

        # Entities
        self.player = Player(x=80, ground_y=self.ground_y)
        

        # Obstacles
        self.obstacles = []
        # --- Obstacle spawning ---
        self.spawn_timer = 0.0

        self.obstacles_passed = 0


        # ===========================================
        # BOUCLE COURTE – Vitesse de déplacement
        # ===========================================
        self.current_speed_level = SPEED_NORMAL

        # ===========================================
        # BOUCLE LONGUE – Adaptation state (loop 2)
        # ===========================================
        self.obstacle_spawn_interval = 3.0   # seconds
        self.min_spawn_interval = 1.5
        self.max_spawn_interval = 5.0

        self.long_term_timer = 0.0
        self.LONG_TERM_WINDOW = 10.0  # seconds

        # ===========================================
        # FIN DE PARCOURS
        # ===========================================        
        self.flag = Flag(
            world_x=3000, # distance de fin
            ground_y=self.ground_y,
        )

        self.session_start_time = time.time()
        self.session_finished = False

        # ===========================================
        # BOUTONS DE FIN DE SESSION
        # ===========================================
        self.restart_button_rect = None
        self.quit_button_rect = None


    # =========================
    # UPDATE
    # =========================
    def update(self, input_manager):
        self.clock.tick(FPS)

        # =========================
        # FREEZE GAME AFTER SESSION
        # =========================
        if self.session_finished:
            return
        
        # ===========================================
        # BOUCLE COURTE
        # Vitesse lente, normale, rapide
        # ===========================================
        # --- Update movement speed from EMG (arm) ---
        activation = input_manager.move_right_pressed()

        # Access temporal stability from input
        arm_stable = False
        if hasattr(input_manager.input, "arm_stable_time"):
            arm_stable = (
                input_manager.input.arm_stable_time
                >= input_manager.input.ARM_STABILITY_THRESHOLD
            )

        # Discrete speed adaptation (no continuous control)
        if arm_stable:
            if activation >= 0.25:
                self.current_speed_level = SPEED_FAST
            elif activation >= 0.15:
                self.current_speed_level = SPEED_NORMAL
            else:
                self.current_speed_level = SPEED_SLOW
        else:
            # Safety fallback if control is unstable
            self.current_speed_level = SPEED_SLOW
            
            
        self.move_speed = self.current_speed_level

        # ===========================================
        # BOUCLE LONGUE – Temporal aggregation
        # ===========================================
        self.long_term_timer += 1.0 / FPS

        if self.long_term_timer >= self.LONG_TERM_WINDOW:
            self._adapt_difficulty(input_manager)
            self.long_term_timer = 0.0

        # ===========================================
        # OBSTACLE SPAWNING (uses loop 2 parameters)
        # ===========================================
        self.spawn_timer += 1.0 / FPS

        if self.spawn_timer >= self.obstacle_spawn_interval:
            self._spawn_obstacle()
            self.spawn_timer = 0.0


        # --- Update obstacle positions ---
        for obstacle in self.obstacles:
            obstacle.update_screen_position(self.world_offset)

        # --- Ground / platform detection ---
        player_on_obstacle = False
        self.player.ground_y = self.ground_y

        for obstacle in self.obstacles:
            foot_left = self.player.rect.left + FOOT_MARGIN
            foot_right = self.player.rect.right - FOOT_MARGIN

            horizontal_ok = (
                foot_right > obstacle.rect.left and
                foot_left < obstacle.rect.right
            )

            if self.player.velocity_y >= 0:
                previous_bottom = self.player.rect.bottom - self.player.velocity_y
                current_bottom = self.player.rect.bottom

                vertical_ok = (
                    previous_bottom <= obstacle.rect.top + PLAYER_FEET_OFFSET
                    and current_bottom >= obstacle.rect.top + PLAYER_FEET_OFFSET
                )

                if horizontal_ok and vertical_ok:
                    self.player.ground_y = obstacle.rect.top + PLAYER_FEET_OFFSET
                    self.player.velocity_y = 0
                    player_on_obstacle = True
                    break

        # --- Horizontal collision (blocking) ---
        blocked = False
        if input_manager.move_right_pressed():
            future_rect = self.player.rect.copy()
            future_rect.x += self.move_speed

            for obstacle in self.obstacles:
                if future_rect.colliderect(obstacle.rect):
                    if obstacle.rect.left >= self.player.rect.right:
                        if (
                            self.player.rect.bottom
                            > obstacle.rect.top + 5
                            and not player_on_obstacle
                        ):
                            blocked = True
                            break

        # --- World movement ---
        if input_manager.move_right_pressed() and not blocked:
            self.world_offset += self.move_speed
            self.player.set_moving(True)
            self.player.world_x = self.world_offset
        else:
            self.player.set_moving(False)

        # --- Physics ---
        self.player.update()

        # --- count passed obstacles ---
        for obstacle in self.obstacles:
            if not obstacle.passed:
                if obstacle.world_x + obstacle.width < self.player.world_x:
                    obstacle.passed = True
                    self.obstacles_passed += 1

        # --- Update flag position ---
        self.flag.update_screen_position(self.world_offset)

        # --- Check end of session ---
        if not self.session_finished:
            if self.player.world_x >= self.flag.world_x:
                self.session_finished = True
                self.session_time = time.time() - self.session_start_time
                print("🏁 FIN DE SESSION")
                print("Temps :", round(self.session_time, 2))
                print("Obstacles :", self.obstacles_passed)


        if self.session_finished:
            return



    # =========================
    # DRAW
    # =========================
    def draw(self):
        self._draw_background()

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        self.flag.draw(self.screen)
        self.player.draw(self.screen)
        
        if self.session_finished:
            self.draw_end_session_overlay()


    # =========================
    # BACKGROUND
    # =========================
    def _draw_background(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        sky_scaled = pygame.transform.scale(
            self.sky_img, (screen_width, screen_height)
        )
        self.screen.blit(sky_scaled, (0, 0))

        ground_width = self.ground_img.get_width()
        ground_height = self.ground_img.get_height()
        y = screen_height - ground_height

        start_x = -int(self.world_offset % ground_width)
        for x in range(start_x, screen_width, ground_width):
            self.screen.blit(self.ground_img, (x, y))


    # ===================================================
    # ADAPT DIFFICULTY (LOOP 2)
    # ===================================================
    def _adapt_difficulty(self, input_manager):
        """
        ===========================================
        BOUCLE LONGUE – Difficulty adaptation (loop 2)
        Adapt obstacle frequency based on control quality
        ===========================================
        """

        # Retrieve control precision from EMG input
        if hasattr(input_manager.input, "get_control_precision"):
            control_precision = input_manager.input.get_control_precision()
        else:
            return

        # Target control zone (from design document)
        if control_precision < 0.4:
            # Control is unstable → reduce difficulty
            self.obstacle_spawn_interval = min(
                self.obstacle_spawn_interval + 0.5,
                self.max_spawn_interval
            )

        elif control_precision > 0.7:
            # Control is stable → increase difficulty
            self.obstacle_spawn_interval = max(
                self.obstacle_spawn_interval - 0.5,
                self.min_spawn_interval
            )

        # Else: keep current difficulty

    def _spawn_obstacle(self):
        """
        Spawn a new obstacle at a fixed distance ahead.
        Difficulty is controlled by obstacle_spawn_interval
        (long-term adaptation loop).
        """

        spawn_x = self.world_offset + self.screen.get_width() + 100

        width = random.choice([50, 60, 70])
        height = random.choice([50, 60, 80])

        obstacle = Obstacle(
            world_x=spawn_x,
            ground_y=self.ground_y,
            width=width,
            height=height
        )

        self.obstacles.append(obstacle)

    # ===================================================
    # END OF SESSION
    # ===================================================
    def draw_end_session_overlay(self):
        # --- Dark transparent overlay ---
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # black with alpha
        self.screen.blit(overlay, (0, 0))

        # --- Result box ---
        box_width = 400
        box_height = 220
        box_x = (self.screen.get_width() - box_width) // 2
        box_y = (self.screen.get_height() - box_height) // 2

        pygame.draw.rect(
            self.screen,
            (240, 240, 240),
            (box_x, box_y, box_width, box_height),
            border_radius=12
        )

        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            (box_x, box_y, box_width, box_height),
            2,
            border_radius=12
        )

        # --- Text ---
        font_title = pygame.font.Font(None, 42)
        font_text = pygame.font.Font(None, 32)

        title = font_title.render("Session finished", True, (0, 0, 0))
        time_text = font_text.render(
            f"Time: {round(self.session_time, 2)} s", True, (0, 0, 0)
        )
        obstacles_text = font_text.render(
            f"Obstacles passed: {self.obstacles_passed}", True, (0, 0, 0)
        )

        self.screen.blit(title, (box_x + 100, box_y + 25))
        self.screen.blit(time_text, (box_x + 40, box_y + 100))
        self.screen.blit(obstacles_text, (box_x + 40, box_y + 140))

        # --- Buttons ---
        button_width = 140
        button_height = 45
        button_y = box_y + 170

        restart_x = box_x + 40
        quit_x = box_x + box_width - button_width - 40

        self.restart_button_rect = pygame.Rect(
            restart_x, button_y, button_width, button_height
        )
        self.quit_button_rect = pygame.Rect(
            quit_x, button_y, button_width, button_height
        )

        pygame.draw.rect(self.screen, (80, 170, 80), self.restart_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (170, 80, 80), self.quit_button_rect, border_radius=8)

        font_button = pygame.font.Font(None, 30)

        restart_text = font_button.render("Restart", True, (255, 255, 255))
        quit_text = font_button.render("Quit", True, (255, 255, 255))

        self.screen.blit(
            restart_text,
            restart_text.get_rect(center=self.restart_button_rect.center)
        )
        self.screen.blit(
            quit_text,
            quit_text.get_rect(center=self.quit_button_rect.center)
        )

