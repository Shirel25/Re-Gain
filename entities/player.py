# entities/player.py
import pygame
from config import GRAVITY, JUMP_FORCE

class Player:
    def __init__(self, x, ground_y):
        self.ground_y = ground_y

        # --- Load sprites ---
        self.idle_image = self.load_sprite("assets/sprites/player/idle.png")
        self.walk_images = [
            self.load_sprite("assets/sprites/player/walk_1.png"),
            self.load_sprite("assets/sprites/player/walk_2.png"),
        ]
        self.jump_image = self.load_sprite("assets/sprites/player/jump.png")

        # Animation state
        self.current_image = self.idle_image
        self.walk_index = 0
        self.animation_timer = 0
        self.animation_speed = 10  # lower = faster animation

        # Rect
        self.rect = self.current_image.get_rect()
        self.rect.x = x
        self.rect.bottom = ground_y
        
        # Position
        self.world_x = 0

        # Physics
        self.velocity_y = 0
        self.on_ground = True

        # Movement state
        self.moving = False

    def load_sprite(self, path):
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.flip(image, True, False)  # face right
        image = pygame.transform.scale(image, (70, 90))
        return image

    def update(self):
        # --- Gravity ---
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        # --- Ground collision ---
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # --- Animation state ---
        if not self.on_ground:
            self.current_image = self.jump_image

        elif self.moving:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.walk_index = (self.walk_index + 1) % len(self.walk_images)

            self.current_image = self.walk_images[self.walk_index]

        else:
            self.current_image = self.idle_image


    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_FORCE
            self.on_ground = False

    def set_moving(self, is_moving):
        self.moving = is_moving

    def draw(self, screen):
        screen.blit(self.current_image, self.rect)
