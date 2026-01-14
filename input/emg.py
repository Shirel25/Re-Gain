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
        self.arm_ref = calibration.arm.mod_mean
        # self.arm_ref = calibration.arm.mod_mean if calibration.arm.mod_mean > 1.0 else 1.0
        # self.arm_ref = calibration.arm.max_activation

        self.leg_baseline = calibration.leg.baseline
        self.leg_ref = calibration.leg.mod_mean
        # self.leg_ref = calibration.leg.mod_mean if calibration.leg.mod_mean > 1.0 else 1.0
        # self.leg_ref = calibration.leg.max_activation

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
        # arm_norm = arm_corr / (self.arm_ref + 1e-6)
        # arm_norm = np.clip(arm_norm, 0, 1)
        arm_norm = np.clip(arm_corr / self.arm_ref, 0, 1)

        self.arm_activation += self.alpha * (arm_norm - self.arm_activation)

        if 0.1 <= self.arm_activation <= 0.4:
            self.arm_stable_time += 1 / 60
        else:
            self.arm_stable_time = 0.0

        # ===== LEG =====
        leg = data[:, self.leg_idx]
        leg_env = np.mean(np.abs(leg - np.mean(leg))) * gain 
        
        # simple threshold based on calibration
        self.leg_activation = leg_env > (self.leg_baseline + self.leg_ref)

        # leg_corr = max(0, leg_env - self.leg_baseline)
        # leg_norm = leg_corr / (self.leg_ref + 1e-6)
        # leg_norm = np.clip(leg_norm, 0, 1)

        # self.leg_activation += self.alpha * (leg_norm - self.leg_activation)

        # # Test 
        # print("ARM raw:", arm)
        # print("LEG raw:", leg)

        # print("ARM env:", arm_env, "ARM corr:", arm_corr, "ARM norm:", arm_norm)
        # print("LEG env:", leg_env, "LEG corr:", leg_corr, "LEG norm:", leg_norm)
    
        # print("Calibration arm_baseline:", self.arm_baseline)
        # print("Calibration arm_ref:", self.arm_ref)
        # print("Calibration leg_baseline:", self.leg_baseline)
        # print("Calibration leg_ref:", self.leg_ref)

        arm_raw = data[:, self.arm_idx]
        leg_raw = data[:, self.leg_idx]

        # print(
        #     f"ARM raw min/max: {arm_raw.min():.1f}/{arm_raw.max():.1f} | "
        #     f"LEG raw min/max: {leg_raw.min():.1f}/{leg_raw.max():.1f}",
        #     end="\r"
        # )

        # print(
        #     f"ARM env={arm_env:.2f} | corr={arm_corr:.2f} | norm={arm_norm:.2f} | act={self.arm_activation:.2f}"
        # )


    def move_right_pressed(self):
        if self.arm_stable_time >= self.ARM_STABILITY_THRESHOLD:
            return self.arm_activation
        return 0.0
        # return self.arm_activation > 0.3

    def jump_pressed(self):
        # return self.leg_activation > 0.3
        return self.leg_activation 

    def close(self):
        self.device.stop()
        self.device.close()
