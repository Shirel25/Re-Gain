import pygame
import random
from Classes.Config import Y_GROUND, OBSTACLE_SPEED


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, type):
        super().__init__()

        y_pos = 0
        if type == 'fly':
            self.frames = [
                pygame.transform.rotozoom(pygame.image.load('Graphics/Fly/Fly1.png').convert_alpha(), 0, 1.2),
                pygame.transform.rotozoom(pygame.image.load('Graphics/Fly/Fly2.png').convert_alpha(), 0, 1.2)
            ]
            y_pos = Y_GROUND - 135

        elif type == 'snail':
            self.frames = [
                pygame.transform.rotozoom(pygame.image.load('Graphics/Snail/snail1.png').convert_alpha(), 0, 1),
                pygame.transform.rotozoom(pygame.image.load('Graphics/Snail/snail2.png').convert_alpha(), 0, 1)
            ]
            y_pos = Y_GROUND
            
        self.animation_index = 0
        self.animation_speed = OBSTACLE_SPEED

        self.image = self.frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom = (random.randint(1800, 2200), y_pos))
        self.hitbox = self.rect.inflate(-12, -12)

    
    def handle_movement(self): # animation
        self.animation_index += 0.1
        if self.animation_index >= len(self.frames):
            self.animation_index = 0
        self.image = self.frames[int(self.animation_index)]

        self.rect.x -= self.animation_speed
        self.hitbox.midbottom = self.rect.midbottom

    
    def update(self):
        self.handle_movement()
        self.destroy()

    def destroy(self):
        if self.rect.x < -200:
            self.kill()
