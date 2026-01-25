import math
import random


class FakeEMGInput:
    """
    Fake EMG generator used to develop and test the game logic
    without a real EMG sensor.
    """

    def __init__(self, profile="intermediate"):
        self.profile = profile
        self.time = 0.0

        # Normalized activations
        self.leg_activation = 0.0   # jump
        self.arm_activation = 0.0   # movement speed

        # --- Temporal stability ---
        self.arm_stable_time = 0.0
        self.ARM_STABILITY_THRESHOLD = 0.4   # seconds
        
        # -- LEG --
        self.leg_phase = "rest"      # "rest" | "impulse" | "recovery"
        self.leg_timer = 0.0
        # -- ARM --
        self.arm_phase = "rest"      # "rest" | "active" | "overload"
        self.arm_timer = 0.0
        
        
        #  fatigue simulation
        self.sim_fatigue = 0.0         
        self.sim_fatigue_rate = 0.004  
        self.sim_recovery_rate = 0.01
        self.fatigue_enabled = False   # OFF for first session




    def update(self):
        params = self._get_profile_params()
        dt = 1 / 60
        self.time += dt

        # =====================
        # ARM - continuous effort
        # =====================
        base = random.choice(params["arm_levels"])
        noise = random.uniform(-params["noise"], params["noise"])
        self.arm_activation = max(0.0, min(base + noise, 1.0))

        # Stability tracking
        if 0.15 <= self.arm_activation <= 0.5:
            self.arm_stable_time += dt
        else:
            self.arm_stable_time = 0.0

        # =====================
        # LEG - jump impulse
        # =====================
        if self.leg_phase == "rest":
            self.leg_activation = 0.0
            if random.random() < params["jump_prob"]:
                self.leg_phase = "impulse"
                self.leg_timer = 0.15

        elif self.leg_phase == "impulse":
            self.leg_activation = 1.0
            self.leg_timer -= dt
            if self.leg_timer <= 0:
                self.leg_phase = "recovery"
                self.leg_timer = 0.6

        elif self.leg_phase == "recovery":
            self.leg_activation = 0.0
            self.leg_timer -= dt
            if self.leg_timer <= 0:
                self.leg_phase = "rest"
        
        # UPDATED ;
        # =====================
        # Simulated fatigue
        # =====================
        
        if self.fatigue_enabled: 
            if self.arm_activation > 0.25:
                self.sim_fatigue = min(1.0, self.sim_fatigue + self.sim_fatigue_rate)
            else:
                self.sim_fatigue = max(0.0, self.sim_fatigue - self.sim_recovery_rate)

            fatigue_gain = 1.0 - 0.6 * self.sim_fatigue

            if random.random() < self.sim_fatigue * 0.25:
                self.arm_activation *= 0.3
            else:
                self.arm_activation *= fatigue_gain
        else:
            self.sim_fatigue = 0.0
            

        return self.arm_activation, self.leg_activation
        
        
    def _get_profile_params(self):
        if self.profile == "beginner":
            return {
                "arm_levels": [0.05, 0.15, 0.25],
                "noise": 0.08,
                "jump_prob": 0.005
            }

        elif self.profile == "advanced":
            return {
                "arm_levels": [0.25, 0.4, 0.6],
                "noise": 0.02,
                "jump_prob": 0.02
            }

        # intermediate (default)
        return {
            "arm_levels": [0.15, 0.3, 0.45],
            "noise": 0.05,
            "jump_prob": 0.01
        }
        
    def set_fatigue_enabled(self, enabled: bool):
            self.fatigue_enabled = enabled

