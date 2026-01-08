# config.py
# Global configuration for Re:Gain (Mario-like prototype)

# =====================
# Window
# =====================
WIDTH = 900
HEIGHT = 300
FPS = 60
TITLE = "Re:Gain"

# =====================
# Colors (RGB)
# =====================
SKY_BLUE = (200, 230, 255)
GROUND_GREEN = (120, 200, 120)
GROUND_BROWN = (150, 100, 50)
PLAYER_COLOR = (80, 200, 180)
OBSTACLE_COLOR = (120, 120, 120)
TEXT_COLOR = (40, 40, 40)

# =====================
# Ground
# =====================
GROUND_HEIGHT = 60
GROUND_Y = HEIGHT - GROUND_HEIGHT
GROUND_SURFACE_OFFSET = 12

# =====================
# Physics
# =====================
GRAVITY = 0.8
JUMP_FORCE = -12

# =====================
# Player
# =====================
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 40
PLAYER_X = 80
PLAYER_FEET_OFFSET = 10
FOOT_MARGIN = 12

# =====================
# Obstacles
# =====================
OBSTACLE_MIN_WIDTH = 30
OBSTACLE_MAX_WIDTH = 50
OBSTACLE_MIN_HEIGHT = 30
OBSTACLE_MAX_HEIGHT = 60
OBSTACLE_SPEED = 4
OBSTACLE_GROUND_OFFSET = -5
