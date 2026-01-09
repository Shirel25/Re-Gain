import pygame

GROUND_GAP = 6  # pixels above ground

class Flag:
    def __init__(self, world_x, ground_y):
        self.world_x = world_x
        self.width = 14
        self.height = 95

        self.rect = pygame.Rect(
            world_x,
            ground_y - self.height - GROUND_GAP,
            self.width,
            self.height
        )

    def update_screen_position(self, world_offset):
        self.rect.x = self.world_x - world_offset

    def draw(self, screen):
        # Pole
        pygame.draw.rect(screen, (0, 0, 0), self.rect)

        # Flag cloth
        flag_rect = pygame.Rect(
            self.rect.right,
            self.rect.top + 6,
            36,
            24
        )
        pygame.draw.rect(screen, (255, 255, 255), flag_rect)
