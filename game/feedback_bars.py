import pygame

# =========================
# COLORS
# =========================
RED = (200, 60, 60)
YELLOW = (220, 200, 60)
GREEN = (60, 180, 90)
GRAY = (220, 220, 220)


def get_color(value, yellow_th, green_th):
    if value < yellow_th:
        return RED
    elif value < green_th:
        return YELLOW
    else:
        return GREEN


class FeedbackBars:
    """
    UI component displaying EMG feedback bars.
    - Arm: horizontal bar (top)
    - Leg: vertical bar (side)
    """

    def __init__(self):
        self.arm_activation = 0.0  # [0,1]
        self.leg_activation = 0.0  # [0,1]

    def update(self, arm_value, leg_value):
        """
        Update normalized EMG values.
        """
        self.arm_activation = max(0.0, min(arm_value, 1.0))
        self.leg_activation = max(0.0, min(leg_value, 1.0))

    def draw(self, screen):
        # =========================
        # ARM BAR (horizontal, top)
        # =========================
        bar_x = 200
        bar_y = 20
        bar_width = 300
        bar_height = 26

        pygame.draw.rect(
            screen, GRAY,
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=5
        )

        fill_width = int(bar_width * self.arm_activation)
        arm_color = get_color(self.arm_activation, 0.15, 0.30)

        pygame.draw.rect(
            screen, arm_color,
            (bar_x, bar_y, fill_width, bar_height),
            border_radius=5
        )

        # --- Label ---
        font = pygame.font.Font(None, 22)
        arm_label = font.render("ARM:", True, (0, 0, 0))
        screen.blit(arm_label, (bar_x - 50, bar_y + 2))

        # =========================
        # LEG BAR (vertical, side)
        # =========================
        leg_width = 26
        leg_height = 160
        leg_x = screen.get_width() - 40
        leg_y = 120

        pygame.draw.rect(
            screen, GRAY,
            (leg_x, leg_y, leg_width, leg_height),
            border_radius=5
        )

        fill_height = int(leg_height * self.leg_activation)
        leg_color = get_color(self.leg_activation, 0.4, 0.6)

        pygame.draw.rect(
            screen,
            leg_color,
            (
                leg_x,
                leg_y + leg_height - fill_height,
                leg_width,
                fill_height
            ),
            border_radius=5
        )

        # --- Label ---
        leg_label = font.render("LEG:", True, (0, 0, 0))
        screen.blit(leg_label, (leg_x - 10, leg_y - 25))

