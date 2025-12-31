import pygame
from Classes.Config import GROUND_Y, PLAYER_SPEED, WIDTH

class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x=80, pos_y=GROUND_Y):
        super().__init__()
        self.walk = [
            pygame.image.load('Graphics/Player/player_walk_1.png').convert_alpha(),  
            pygame.image.load('Graphics/Player/player_walk_2.png').convert_alpha()
        ]
        self.jump = pygame.image.load('Graphics/Player/jump.png').convert_alpha()
        self.stand = pygame.image.load('Graphics/Player/player_stand.png').convert_alpha()
        self.scaled = pygame.transform.rotozoom(self.stand, 0, 2)
        self.image = self.stand
        self.rect = self.image.get_rect(midbottom=(pos_x, pos_y))
        self.gravity = 0
        self.walk_index = 0
        self.moving = False


    def player_input(self):
        keys = pygame.key.get_pressed()
        self.moving = False

        if keys[pygame.K_RIGHT]:
            if self.rect.right <= WIDTH:
                self.rect.right += PLAYER_SPEED
                self.moving = True 

        if keys[pygame.K_LEFT]:
            if self.rect.left >= 0:
                self.rect.right -= PLAYER_SPEED
                self.moving = True

        if keys[pygame.K_SPACE]:
            if self.rect.bottom == GROUND_Y:
                self.gravity = -20


    def handle_movement(self):
        self.image = self.stand
        # Gravity for jumping
        if self.rect.bottom < GROUND_Y:
            self.gravity += 1
            self.rect.y += self.gravity
            self.image = self.jump

        # Update walking animation
        elif self.rect.bottom == GROUND_Y:
            if self.gravity < 0: # first frame of jump
                self.gravity += 1
                self.rect.y += self.gravity
                self.image = self.jump

            if self.moving:
                self.walk_index += 0.1
                if self.walk_index >= len(self.walk):
                    self.walk_index = 0
                self.image = self.walk[int(self.walk_index)]

        # Neutral position
        else:  
            self.rect.bottom = GROUND_Y


    def update(self):
        self.player_input()
        self.handle_movement()