import math
import random


class FakeEMGInput:
    """
    Fake EMG generator used to develop and test the game logic
    without a real EMG sensor.
    """

    def __init__(self):
        self.time = 0.0

        # Normalized activations
        self.leg_activation = 0.0   # jump
        self.arm_activation = 0.0   # movement speed

        # --- Temporal stability ---
        self.arm_stable_time = 0.0
        self.ARM_STABILITY_THRESHOLD = 0.4   # seconds

    def update(self):
        """
        Simulate EMG signals over time.
        """
        # ===========================================
        # BOUCLE COURTE – Signal interpretation
        # Filtering, stability, safety
        # ===========================================
        self.time += 0.05

        # --- Arm: smooth continuous effort ---
        self.arm_activation = 0.2

        # --- Leg: occasional contraction peaks ---
        if random.random() < 0.02:
            self.leg_activation = 1.0
        else:
            self.leg_activation = 0.0
        
        # --- Update temporal stability for arm ---
        if 0.10 <= self.arm_activation <= 0.30:
            self.arm_stable_time += 0.05   # dt ≈ frame duration
        else:
            self.arm_stable_time = 0.0


    # ===== Interface compatible with InputManager =====

    def jump_pressed(self, threshold=0.6):
        return self.leg_activation > threshold

    def move_right_pressed(self):
        """
        Continuous control allowed only if activation
        is temporally stable.
        """
        if self.arm_stable_time >= self.ARM_STABILITY_THRESHOLD:
            return max(0.0, min(self.arm_activation, 1.0))
        return 0.0
    
