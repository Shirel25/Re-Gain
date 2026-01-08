import pygame


class KeyboardInput:
    def __init__(self):
        self.jump = False
        self.move_right = False

    def update(self, events):
        # Saut
        self.jump = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.jump = True

        # Déplacement à droite
        keys = pygame.key.get_pressed()
        self.move_right = keys[pygame.K_RIGHT]

    def jump_pressed(self):
        return self.jump
    
    def move_right_pressed(self):
        return self.move_right

