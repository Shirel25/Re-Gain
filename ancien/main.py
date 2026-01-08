import pygame
from random import choice, random
from Classes.Player import Player
from Classes.Obstacle import Obstacle
from Classes.Interface import Interface
from Classes.UserModel import UserModel
from Classes.Config import WIDTH, HEIGHT, Y_GROUND, PLAYER_SPEED, OBSTACLE_SPEED

"""
reste à faire : Input Capteurs, User Model, Ajout de Menu, Sound, Choix de personnage, Add coins, Dashboard, 
                Ajout de puit (comme dans Mario) et animation de game over (circle noir qui entoure le caractère)

Pour le User Model:
    Traces : 
        - performance : taux de réussite, collisions/min, score
        - précision motrice : variabilité du timing (sauts trop tôt/trop tard)
        - effort (EMG) : moyenne, pics, asymétrie gauche/droite
        - fatigue : effort qui monte + performance qui baisse
        - niveau estimé : débutant/intermédiaire/avancé (même via seuils)

    Adaptation : 
        - vitesse des obstacles (OBSTACLE_SPEED)
        - fréquence de spawn (set_timer(obstacle_timer, ms))
        - proportion d’obstacles difficiles (plus de “fly”, patterns plus denses)
        - largeur effective des obstacles (hitbox), si tu veux le faire
"""

def player_obstacle_handling(player, obstacles):
    """
    - Checks to see if there has been a collision (game over)
    - Adjust obstacle speed relative to player
    """
    for obstacle in obstacles.sprites():
        # For debugging the jump
        # pygame.draw.rect(screen, "red", player.sprite.hitbox, 2)
        # pygame.draw.rect(screen, "blue", obstacle.hitbox, 2)

        overlap = player.sprite.hitbox.clip(obstacle.hitbox)
        if overlap.width > 0 and overlap.height > 0:
            if overlap.width * overlap.height > 20: 
                return False

        # # Camera fixed on the player
        # if player.sprite.moving: obstacle.animation_speed = PLAYER_SPEED + OBSTACLE_SPEED
        # else:                    obstacle.animation_speed = OBSTACLE_SPEED
        
        obstacle.animation_speed = OBSTACLE_SPEED

    return True


def main():
    user_model = UserModel()

    pygame.init()
    pygame.display.set_caption("Re:Gain")

    clock = pygame.time.Clock() 
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.Font('Fonts/Pixeltype.ttf', 50)

    sky = pygame.transform.rotozoom(pygame.image.load('Graphics/Sky.png').convert(), 0, 2)
    ground = pygame.transform.rotozoom(pygame.image.load('Graphics/ground.png').convert(), 0, 2)

    # ------------------------
    # SCROLLING OFFSETS 
    # ------------------------
    sky_x = 0
    ground_x = 0

    running = True
    game_active = False

    interface = Interface(screen, font)

    player = pygame.sprite.GroupSingle()
    player.add(Player())  # Player déjà repositionné plus à droite

    obstacle_groupe = pygame.sprite.Group()

    obstacle_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(obstacle_timer, 3500)

    running = True
    game_active = False

    interface = Interface(screen, font)
    player = pygame.sprite.GroupSingle()
    player.add(Player())
    obstacle_groupe = pygame.sprite.Group()
    obstacle_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(obstacle_timer, 3500) 

    # ----------------------------------
    # MAIN LOOP
    # ----------------------------------
    while running: 

        for event in pygame.event.get(): 

            if event.type == pygame.QUIT:
                running = False
                break
            
            if game_active:
                if event.type == obstacle_timer:
                    obstacle_groupe.add(Obstacle(choice(['fly', 'snail', 'snail', 'snail']))) # 25% fly, 75% snail

            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_active = True
                    interface.restart()
            
        
        if game_active:
            # -------------------------
            # SCROLL UPDATE
            # -------------------------
            if player.sprite.moving or player.sprite.is_jumping:
                scroll_speed = PLAYER_SPEED

                sky_x -= scroll_speed * 0.3     # parallax
                ground_x -= scroll_speed
            

            # -------------------------
            # DRAW SKY 
            # -------------------------
            screen.blit(sky, (sky_x, 0))
            screen.blit(sky, (sky_x + sky.get_width(), 0))
            if sky_x <= -sky.get_width():
                sky_x = 0

            # -------------------------
            # DRAW GROUND
            # -------------------------
            screen.blit(ground, (ground_x, Y_GROUND))
            screen.blit(ground, (ground_x + ground.get_width(), Y_GROUND))
            if ground_x <= -ground.get_width():
                ground_x = 0


            # ----------------------------------
            # TEMPORARY EMG INPUT (mock)
            # ----------------------------------
            activation_norm = random() * 0.4  # simulate EMG activation in [0, 0.4]
            user_model.update_from_emg(activation_norm)

            # ----------------------------------
            # UPDATE GAME OBJECTS
            # ----------------------------------
            player.draw(screen)
            player.update()

            obstacle_groupe.draw(screen)
            obstacle_groupe.update()

            game_active = player_obstacle_handling(player, obstacle_groupe)

            # ----------------------------------
            # DEBUG: observe user model state
            # ----------------------------------
            short_state = user_model.get_short_term_state()
            long_state = user_model.get_long_term_state()

            print(
                f"EMG act: {short_state['activation']:.2f} | "
                f"Prec: {short_state['precision']:.2f} | "
                f"Fatigue: {long_state['fatigue']:.2f}"
            )


            interface.update(game_active)

        else:
            interface.update(game_active)

            player.empty()
            player.add(Player())
            obstacle_groupe.empty()
            
        pygame.display.flip() 
        clock.tick(60) 

    pygame.quit()

if __name__ == "__main__":
    main()