# input/emg.py
from bitalino import BITalino
import numpy as np

class EMGInput:
    def __init__(
        self,
        device,
        baseline=0.0,
        max_activation=1.0,
        window_size=300,
        gain=10,
        alpha=0.8,
    ):
        self.device = device

        self.window_size = window_size
        self.gain = gain
        self.alpha = alpha

        self.baseline = baseline
        self.max_activation = max_activation

        self.activation_prev = 0.0
        self.current_activation = 0.0


    def update(self):
        data = self.device.read(self.window_size)
        emg = data[:, -1]

        emg = emg - np.mean(emg)
        emg_rect = np.abs(emg)
        envelope = np.mean(emg_rect)

        activation = envelope * self.gain
        activation_smooth = (
            self.alpha * self.activation_prev
            + (1 - self.alpha) * activation
        )
        self.activation_prev = activation_smooth

        # Normalisation
        activation_norm = max(
            0.0,
            (activation_smooth - self.baseline) / self.max_activation
        )

        self.current_activation = min(activation_norm, 1.0)

    def jump_pressed(self, threshold=0.6):
        return self.current_activation > threshold

    def move_right_pressed(self, threshold=0.2):
        return self.current_activation > threshold

    def close(self):
        self.device.stop()
        self.device.close()

# ====================================================================

class DualEMGInput:
    def __init__(self, device, arm_channel, leg_channel, calibration):
        self.device = device

        # analog channels are at the end of the frame
        self.arm_idx = -2 #A5
        self.leg_idx = -1 #A2

        self.arm_baseline = calibration.arm.baseline
        self.arm_ref = calibration.arm.max_activation
        

        self.leg_baseline = calibration.leg.baseline
        self.leg_ref = calibration.leg.max_activation
        
        self.arm_activation = 0.0
        self.leg_activation = 0.0

        self.alpha = 0.35
        self.arm_stable_time = 0.0
        self.ARM_STABILITY_THRESHOLD = 0.4
        

    def update(self):
        data = self.device.read(250)
        gain = 10 

        # ===== ARM =====
        arm = data[:, self.arm_idx]
        arm_env = np.mean(np.abs(arm - np.mean(arm))) * gain
        arm_corr = max(0, arm_env - self.arm_baseline)
        arm_norm = np.clip(arm_corr / self.arm_ref, 0, 1)

        self.arm_activation += self.alpha * (arm_norm - self.arm_activation)


        # ===== LEG =====
        leg = data[:, self.leg_idx]
        leg_env = np.mean(np.abs(leg - np.mean(leg))) * gain 
        leg_corr = max(0, leg_env - self.leg_baseline)
        leg_norm = np.clip(leg_corr / self.leg_ref, 0, 1)
        
        self.leg_activation += self.alpha * (leg_norm - self.leg_activation)

        return self.arm_activation, self.leg_activation
    

    def close(self):
        self.device.stop()
        self.device.close()
