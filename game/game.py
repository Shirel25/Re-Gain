import pygame

from config import FPS, GROUND_SURFACE_OFFSET, FOOT_MARGIN, PLAYER_FEET_OFFSET
from entities.player import Player
from entities.obstacle import Obstacle


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

        self.obstacles = [
            Obstacle(world_x=400, ground_y=self.ground_y, width=60, height=80),
            Obstacle(world_x=700, ground_y=self.ground_y, width=80, height=70),
            Obstacle(world_x=1000, ground_y=self.ground_y, width=60, height=60),
        ]

    # =========================
    # UPDATE
    # =========================
    def update(self, input_manager):
        self.clock.tick(FPS)

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

            vertical_ok = (
                abs(
                    self.player.rect.bottom
                    - (obstacle.rect.top + PLAYER_FEET_OFFSET)
                ) <= 5
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

    # =========================
    # DRAW
    # =========================
    def draw(self):
        self._draw_background()

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

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

        start_x = -(self.world_offset % ground_width)
        for x in range(start_x, screen_width, ground_width):
            self.screen.blit(self.ground_img, (x, y))
