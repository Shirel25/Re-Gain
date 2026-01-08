# entities/obstacle.py
import pygame
from config import OBSTACLE_GROUND_OFFSET

class Obstacle:
    def __init__(self, world_x, ground_y, width, height):
        self.world_x = world_x

        self.ground_y = ground_y  # store collision ground

        self.rect = pygame.Rect(
            0,
            self.ground_y - height + OBSTACLE_GROUND_OFFSET,
            width,
            height
        )


    def update_screen_position(self, world_offset):
        self.rect.x = self.world_x - world_offset

    def draw(self, screen):
        pygame.draw.rect(screen, (80, 180, 80), self.rect)
