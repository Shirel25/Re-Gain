import numpy as np
from collections import deque # for maintaining history buffers, fenetre glissante


class UserModel:
    """
    User model based on EMG-derived features.
    This class estimates the physiological and motor state of the user
    and provides indicators for game adaptation.
    """

    def __init__(
        self,
        history_size=200,       # short window, ~3s at 60Hz
        fatigue_window=1000,    # long window, ~16s at 60Hz
        alpha_activation=0.2
    ):
        # --- Instantaneous values ---
        self.activation = 0.0              # current normalized activation [0, 1]
        self.activation_smooth = 0.0    # smoothed activation

        # --- History buffers ---
        self.activation_history = deque(maxlen=history_size)
        self.long_history = deque(maxlen=fatigue_window)

        # --- User state estimates ---
        self.mean_activation = 0.0
        self.precision = 0.0               # stability of activation
        self.fatigue = 0.0                 # slow trend indicator

        # --- Parameters ---
        self.alpha = alpha_activation      # smoothing factor

    # ======================================================
    # Update from EMG
    # ======================================================
    def update_from_emg(self, activation_norm):
        """
        Update the user model from normalized EMG activation.
        activation_norm must be in [0, 1].
        """

        # Exponential smoothing (robust to noise)
        self.activation_smooth = (
            self.alpha * activation_norm
            + (1 - self.alpha) * self.activation_smooth
        )

        self.activation = self.activation_smooth

        # Update histories
        self.activation_history.append(self.activation)
        self.long_history.append(self.activation)

        # Update derived parameters
        self._update_mean_activation()
        self._update_precision()
        self._update_fatigue()

    # ======================================================
    # Internal computations
    # ======================================================
    def _update_mean_activation(self):
        if len(self.activation_history) > 0:
            self.mean_activation = np.mean(self.activation_history)

    def _update_precision(self):
        """
        Precision = inverse of activation variability.
        Low variance => good motor control.
        """
        if len(self.activation_history) > 10:
            variance = np.var(self.activation_history)
            self.precision = 1.0 / (variance + 1e-6)
        else:
            self.precision = 0.0

    def _update_fatigue(self):
        """
        Fatigue is estimated as a slow drift:
        increasing effort for similar performance.
        """
        if len(self.long_history) > 50:
            recent = np.mean(list(self.long_history)[-50:])
            earlier = np.mean(list(self.long_history)[:50])

            # fatigue grows if effort increases over time
            self.fatigue = max(0.0, recent - earlier)

    # ======================================================
    # Outputs for adaptation
    # ======================================================
    def get_short_term_state(self):
        """
        Used for real-time (intra-phase) adaptation.
        """
        return {
            "activation": self.activation,
            "precision": self.precision
        }

    def get_long_term_state(self):
        """
        Used for inter-phase adaptation.
        """
        return {
            "mean_activation": self.mean_activation,
            "precision": self.precision,
            "fatigue": self.fatigue
        }
