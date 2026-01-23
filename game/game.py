# ================================================================
# GAME LOOP
# - BOUCLE COURTE (loop 1): adaptation en temps réel
#   -> interprétation du signal EMG
#   -> vitesse de déplacement discrète (lente, normale, rapide)
#
# - BOUCLE LONGUE (loop 2): adaptation progressive de la difficulté
#   -> apparition d'obstacles plus ou moins fréquente

# ---------------------------------------------------------------

# Game is responsible for:
# - applying player intentions (move / jump)
# - managing the environment
# - adapting difficulty over time (loop 2)
# All control interpretation is handled by InputManager.
# 
# ================================================================

import pygame
import random
import time

from config import FPS, GROUND_SURFACE_OFFSET, FOOT_MARGIN, PLAYER_FEET_OFFSET
from entities.player import Player
from entities.obstacle import Obstacle
from input.input_manager import InputManager
from entities.flag import Flag
from game.feedback_bars import FeedbackBars


# ===========================================
# BOUCLE COURTE
# Application des niveaux de vitesse discrets
# (décidés dans InputManager à partir de l'EMG)
# ===========================================

SPEED_SLOW = 3.0
SPEED_NORMAL = 5.5
SPEED_FAST = 8.0


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
        self.last_spawn_x = 0
        self.min_obstacle_distance = 160
        self.max_obstacles_on_screen = 6
        self.last_jump_obstacle = None


        # --- Feedback bars ---
        self.feedback_bars = FeedbackBars()
        self.arm_feedback_value = 0.0
        self.leg_feedback_value = 0.0

        # ===========================================
        # BOUCLE COURTE – Vitesse de déplacement
        # ===========================================
        self.current_speed_level = SPEED_NORMAL
        self.displayed_speed_level = 0


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
        # BOUCLE COURTE - appliquée depuis InputManager
        # ===========================================
        if input_manager.move_right_pressed():
            self.move_speed = input_manager.move_speed
        else:
            self.move_speed = 0.0

            

        # =========================
        # FEEDBACK BARS 
        # =========================
        # ARM target value (from speed)
        arm_target = min(
            input_manager.move_speed / input_manager.SPEED_BOOST,
            1.0
        )



        # Smooth transition (EMA)
        alpha = 0.15  # smoothing factor
        self.arm_feedback_value += alpha * (arm_target - self.arm_feedback_value)

        arm_activation = self.arm_feedback_value


        # LEG feedback = progressive jump effort
        if not self.player.on_ground:
            # montée progressive pendant le saut
            self.leg_feedback_value = min(self.leg_feedback_value + 0.08, 1.0)
        else:
            # redescente douce au repos
            self.leg_feedback_value = max(self.leg_feedback_value - 0.05, 0.0)

        leg_activation = self.leg_feedback_value


        self.feedback_bars.update(arm_activation, leg_activation)

        # ===========================================
        # BOUCLE LONGUE – Temporal aggregation
        # ===========================================
        self.long_term_timer += 1.0 / FPS

        if self.long_term_timer >= self.LONG_TERM_WINDOW:
            self._adapt_difficulty(input_manager)
            input_manager.reset_long_term_metrics()
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

        # === Jump ===
        obstacle = self._nearest_obstacle_ahead()
        if (
            input_manager.jump_pressed()
            and self.player.on_ground
            and obstacle is not None
            and obstacle is not self.last_jump_obstacle
        ):
            self.player.jump()
            self.last_jump_obstacle = obstacle


        # --- Ground / platform detection ---
        # player_on_obstacle = False
        # self.player.ground_y = self.ground_y

        # for obstacle in self.obstacles:
        #     # Zone des pieds du joueur
        #     foot_left = self.player.rect.left + FOOT_MARGIN
        #     foot_right = self.player.rect.right - FOOT_MARGIN

        #     horizontal_ok = (
        #         foot_right > obstacle.rect.left + 5 and
        #         foot_left < obstacle.rect.right - 5 
        #     )

        #     if self.player.velocity_y >= 0:
        #         previous_bottom = self.player.rect.bottom - self.player.velocity_y
        #         current_bottom = self.player.rect.bottom

        #         vertical_ok = (
        #             previous_bottom <= obstacle.rect.top + PLAYER_FEET_OFFSET
        #             and current_bottom >= obstacle.rect.top + PLAYER_FEET_OFFSET
        #         )

        #         if horizontal_ok and vertical_ok:
        #             self.player.ground_y = obstacle.rect.top + PLAYER_FEET_OFFSET
        #             self.player.velocity_y = 0
        #             player_on_obstacle = True
        #             break

        player_on_obstacle = False
        support_y = self.ground_y  # sol par défaut

        previous_bottom = self.player.rect.bottom - self.player.velocity_y
        current_bottom = self.player.rect.bottom

        for obstacle in self.obstacles:
            # zone des pieds
            foot_left = self.player.rect.left + FOOT_MARGIN
            foot_right = self.player.rect.right - FOOT_MARGIN

            horizontal_ok = (
                foot_right > obstacle.rect.left + 5 and
                foot_left < obstacle.rect.right - 5
            )

            if not horizontal_ok:
                continue

            # uniquement si le joueur tombe
            if self.player.velocity_y >= 0:
                obstacle_top = obstacle.rect.top + PLAYER_FEET_OFFSET

                vertical_ok = (
                    previous_bottom <= obstacle_top and
                    current_bottom >= obstacle_top
                )

                if vertical_ok:
                    # on garde la surface la plus haute
                    if obstacle_top < support_y:
                        support_y = obstacle_top
                        player_on_obstacle = True

        if current_bottom >= support_y and self.player.velocity_y >= 0:
            self.player.rect.bottom = support_y
            self.player.velocity_y = 0
            self.player.on_ground = True
        else:
            self.player.on_ground = False

        self.player.ground_y = support_y


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
        # === Move forward ===
        if input_manager.move_right_pressed() and not blocked:
            self.world_offset += self.move_speed
            self.player.set_moving(True)
            self.player.world_x = self.world_offset
        else:
            self.player.set_moving(False)

        # # === Jump ===
        # obstacle = self._nearest_obstacle_ahead()
        # if (
        #     input_manager.jump_pressed()
        #     and self.player.on_ground
        #     and obstacle is not None
        #     and obstacle is not self.last_jump_obstacle
        # ):
        #     self.player.jump()
        #     self.last_jump_obstacle = obstacle


        # --- Physics ---
        self.player.update()

        # --- count passed obstacles ---
        for obstacle in self.obstacles:
            if not obstacle.passed:
                if obstacle.world_x + obstacle.width < self.player.world_x:
                    obstacle.passed = True
                    self.obstacles_passed += 1
                    if obstacle == self.last_jump_obstacle:
                        self.last_jump_obstacle = None

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
    def draw(self, input_manager):
        self._draw_background()

        for obstacle in self.obstacles:
            if obstacle.world_x < self.flag.world_x:
                obstacle.draw(self.screen)

        self.flag.draw(self.screen)
        self.player.draw(self.screen)
        self.feedback_bars.draw(self.screen)
        self._draw_hud(input_manager)

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

    def _draw_hud(self, input_manager):
        font = pygame.font.Font(None, 28)

        # -----------------------------
        # SPEED LEVEL (loop 1)
        # -----------------------------
        if self.move_speed < 0.2:
            speed_level = 0
        elif self.move_speed < 1.4:
            speed_level = 1
        else:
            speed_level = 2

        # -----------------------------
        # DIFFICULTY LEVEL (loop 2)
        # -----------------------------
        difficulty = input_manager.get_difficulty_score()

        if difficulty < 0.33:
            diff_label = "Beginner"
        elif difficulty < 0.66:
            diff_label = "Intermediate"
        else:
            diff_label = "Advanced"

        # --- Smooth display transition --- 
        target_speed = speed_level
        self.displayed_speed_level += 0.2 * (target_speed - self.displayed_speed_level)
        speed_level_display = round(self.displayed_speed_level)

        # -----------------------------
        # Render
        # -----------------------------
        speed_text = font.render(f"Speed: {speed_level_display}", True, (20, 20, 20))
        diff_text = font.render(f"Difficulty: {diff_label}", True, (20, 20, 20))

        self.screen.blit(speed_text, (20, 20))
        self.screen.blit(diff_text, (20, 50))


    # ===================================================
    # ADAPT DIFFICULTY (LOOP 2)
    # ===================================================
    def _adapt_difficulty(self, input_manager):
        difficulty = input_manager.get_difficulty_score()

        performance = min(self.obstacles_passed / 6, 1.0)

        global_difficulty = 0.7 * difficulty + 0.3 * performance

        # --- Spawn frequency ---
        self.obstacle_spawn_interval = (
            self.max_spawn_interval
            - global_difficulty * (self.max_spawn_interval - self.min_spawn_interval)
        )

        # --- Distance between obstacles ---
        self.min_obstacle_distance = int(
            220 - difficulty * 120
        )

        # --- Max simultaneous obstacles ---
        self.max_obstacles_on_screen = int(
            2 + difficulty * 4
        )

        precision = input_manager.get_control_precision()
        speed = input_manager.get_mean_speed()
        difficulty = input_manager.get_difficulty_score()

        print(
            f"[LONG LOOP] "
            f"precision={precision:.2f} | "
            f"speed={speed:.2f} | "
            f"difficulty={difficulty:.2f} | "
            f"spawn={self.obstacle_spawn_interval:.2f} | "
            f"dist={self.min_obstacle_distance} | "
            f"max_obs={self.max_obstacles_on_screen}"
        )



    def _spawn_obstacle(self):
        """
        Spawn a new obstacle ahead of the player.
        Fully constrained by long-loop adaptation.
        """

        # Ne jamais spawn après le drapeau
        if self.world_offset >= self.flag.world_x - 200:
            return

        # Trop d'obstacles déjà présents
        if len(self.obstacles) >= self.max_obstacles_on_screen:
            return

        # === Calculer spawn_x  ===
        min_gap = 180 if self.obstacle_spawn_interval > 4.0 else 120
        spawn_x = max(
            self.last_spawn_x + min_gap,
            self.world_offset + self.screen.get_width() + 100
        )

        # === Respecter la distance minimale ===
        if self.obstacles:
            last = self.obstacles[-1]
            if spawn_x - last.world_x < self.min_obstacle_distance:
                return

        self.last_spawn_x = spawn_x

        # === Créer l'obstacle ===
        width = random.choice([50, 60, 70])
        height = random.choice([50, 60, 80])

        obstacle = Obstacle(
            world_x=spawn_x,
            ground_y=self.ground_y,
            width=width,
            height=height
        )

        self.obstacles.append(obstacle)

    def _nearest_obstacle_ahead(self, distance=120):
        nearest = None
        min_dist = float("inf")

        for obs in self.obstacles:
            d = obs.world_x - self.player.world_x
            if 0 < d < distance and d < min_dist:
                min_dist = d
                nearest = obs

        return nearest



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
        font_title = pygame.font.Font("Fonts/Pixeltype.ttf", 42)
        font_text = pygame.font.Font("Fonts/Pixeltype.ttf", 32)

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



