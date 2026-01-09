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
        self.end_distance = 3000  # pixels
        self.session_finished = False

        self.flag = Flag(
            world_x=self.end_distance,
            ground_y=self.ground_y,
        )


    # =========================
    # UPDATE
    # =========================
    def update(self, input_manager):
        self.clock.tick(FPS)

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
        else:
            self.player.set_moving(False)

        # --- Physics ---
        self.player.update()

        # --- Update flag position ---
        self.flag.update_screen_position(self.world_offset)

        # --- Check end of session ---
        if self.player.rect.colliderect(self.flag.rect):
            self.session_finished = True


    # =========================
    # DRAW
    # =========================
    def draw(self):
        self._draw_background()

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        self.flag.draw(self.screen)
        self.player.draw(self.screen)
        


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


