# input/emg.py
from bitalino import BITalino
import numpy as np

class EMGInput:
    def __init__(
        self,
        mac_address,
        channel=1,
        sampling_rate=1000,
        window_size=300,
        gain=10,
        alpha=0.8,
        baseline=0.0,
        max_activation=1.0,
    ):
        self.device = BITalino(mac_address)
        self.device.start(sampling_rate, [channel])

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
