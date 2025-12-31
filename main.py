import pygame
from random import randint

"""
We have two types of surfaces : regular surfaces and the display surface.
Display surface : must be unique and is always visible.
Regular surfaces : we can have any amout of these we want, they can only
be displayed when we connect them to the display surface.
"""
"""
Creating text : 
1. Create a font (text style and size)
2. write text on a surface 
3. blit the text surface on the display surface (blit = copier une image (ou surface) sur une autre surface)
"""
"""
To create enemies:
1. we create a list of obstacle rectangles
2. everytime the timer triggers, we add a new rectangle to the list
3. we move every rectangle in the list to the left on every frame
4. we remove the rectangles that have moved out of the screen
"""
"""
Sprite class:
A class that contains a surface and a rectangle and it can be drawn and updated very easily.
"""

def main():

    PLAYER_SPEED = 2
    OBSTACLE_SPEED = 1
    GROUND_Y = 300
    WIDTH, HEIGHT = 800, 400

    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Re:Gain")
    clock = pygame.time.Clock() # limite le FPS et mesure le temps entre frames
    font = pygame.font.Font('Fonts/Pixeltype.ttf', 50)
    running = True
    game_active = False
    start_time = 0

    sky_surface = pygame.image.load('Graphics/Sky.png').convert()
    ground_surface = pygame.image.load('Graphics/ground.png').convert()
    game_name_surface = font.render("Re:Gain", False, (111, 196, 169))
    game_name_rect = game_name_surface.get_rect(center = (400, 50))
    score_surface = font.render("Score : 0", False, "dark green")
    score_rect = score_surface.get_rect(center = (400, 50))
    current_score = 0

    # obstacles
    snail_surface_1 = pygame.image.load('Graphics/Snail/snail1.png').convert_alpha()
    snail_surface_2 = pygame.image.load('Graphics/Snail/snail2.png').convert_alpha()
    fly_surface_1 = pygame.image.load('Graphics/Fly/Fly1.png').convert_alpha()
    fly_surface_2 = pygame.image.load('Graphics/Fly/Fly2.png').convert_alpha()   
    obstacle_rect_list = []
    obstacle_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(obstacle_timer, 3000)

    # player
    player_stand = pygame.image.load('Graphics/Player/player_stand.png').convert_alpha()
    player_jump = pygame.image.load('Graphics/Player/jump.png').convert_alpha()
    player_surface_1 = pygame.image.load('Graphics/Player/player_walk_1.png').convert_alpha()
    player_surface_2 = pygame.image.load('Graphics/Player/player_walk_2.png').convert_alpha()
    player_stand_scaled = pygame.transform.rotozoom(player_stand, 0, 2)
    player_stand_rect = player_stand_scaled.get_rect(center = (400, 200))
    player = player_stand
    player_rect = player.get_rect(midbottom = (80, 300))
    player_gravity = 0
    
    replay_instruction_surface = font.render("Press space to replay", False, (111, 196, 169))
    replay_instruction_rect = replay_instruction_surface.get_rect(center = (400, 320))

    while running: # boucle principale du jeu
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get(): # gestion des événements
            if event.type == pygame.QUIT:
                running = False
                break
            
            if game_active:
                # if event.type == pygame.MOUSEBUTTONDOWN and menu_rect.collidepoint(pygame.mouse.get_pos()): lancer le menu
                # if event.type == pygame.MOUSEMOTION and player_rect.collidepoint(event.pos):
                #     print("collision")

                if event.type == pygame.KEYDOWN:
                    game_active = True
                    if event.key == pygame.K_SPACE and player_rect.bottom == GROUND_Y:
                        player_gravity = -20
                        player_rect.y += player_gravity
                        player = player_jump

                if event.type == obstacle_timer:
                    if randint(0, 2): 
                        obstacle_rect_list.append(snail_surface_1.get_rect(bottomright = (randint(900, 1100), 300)))
                    else:
                        obstacle_rect_list.append(fly_surface_1.get_rect(bottomright = (randint(900, 1100), 210)))

            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_active = True
                    player_rect.midbottom = (80, 300)
                    player_gravity = 0  
                    start_time = pygame.time.get_ticks()
            
        
        if game_active:
            screen.blit(sky_surface, (0,0))
            screen.blit(ground_surface, (0, GROUND_Y))
            current_time = pygame.time.get_ticks() - start_time
            current_score = current_time//1000
            score_surface = font.render(f"Score : {current_score}", False, "dark green")
            score_rect = score_surface.get_rect(center = (400, 50))
            screen.blit(score_surface, score_rect)

            # obstacle handling
            if obstacle_rect_list:
                to_delete = []
                for obstacle_rect in obstacle_rect_list:

                    surface_1 = fly_surface_1
                    surface_2 = fly_surface_2

                    if obstacle_rect.bottom == 300:
                        surface_1 = snail_surface_1
                        surface_2 = snail_surface_2

                    surface = surface_2
                    obstacle_rect.x -= OBSTACLE_SPEED

                    if obstacle_rect.right < 0:
                        to_delete.append(obstacle_rect)

                    if obstacle_rect.right % 20 < 10: 
                        surface = surface_1

                    if player_rect.colliderect(obstacle_rect):
                        game_active = False

                    screen.blit(surface, obstacle_rect)

                for obj in to_delete:
                    obstacle_rect_list.remove(obj)


            # player handling
            keys = pygame.key.get_pressed()
            moving = False
            if keys[pygame.K_RIGHT]:
                if player_rect.right <= WIDTH:
                    player_rect.right += PLAYER_SPEED
                    moving = True

            if keys[pygame.K_LEFT]:
                if player_rect.left >= 0:
                    player_rect.right -= PLAYER_SPEED
                    moving = True

            if player_rect.bottom < GROUND_Y:
                player_gravity += 1
                player_rect.y += player_gravity
                player = player_jump
            elif player_rect.bottom == GROUND_Y:  # only animate walk on the ground
                if moving:
                    if player_rect.right % 80 < 40:
                        player = player_surface_1
                    else:
                        player = player_surface_2
                else:
                    player = player_stand
            else:
                player_rect.bottom = GROUND_Y
                player = player_stand

            screen.blit(player, player_rect)
        
        else:
            screen.fill("light blue")
            screen.blit(game_name_surface, game_name_rect)
            screen.blit(player_stand_scaled, player_stand_rect)
            score_surface = font.render(f"Score : {current_score}", False, (111, 196, 169))
            score_rect = score_surface.get_rect(center = (400, 90))
            if current_score > 0 : screen.blit(score_surface, score_rect)
            screen.blit(replay_instruction_surface, replay_instruction_rect)  
            obstacle_rect_list.clear()
            player_rect.midbottom = (80, 300)
            player_gravity = 0              

            
        # flip() the display to put your work on screen
        pygame.display.flip() # == pygame.display.update()

        #clock.tick(60)  # limits FPS to 60, should not run faster than 60 fps
        clock.tick(60) 

    pygame.quit()

if __name__ == "__main__":
    main()