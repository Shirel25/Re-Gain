# input/emg.py
from bitalino import BITalino
import numpy as np
import collections



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






# ====================================================================
class FatigueTracker:
    """
    Estimates fatigue from EMG activations using windowed statistics.
    """

    def __init__(
        self,
        fps=60,
        window_sec=20.0,
        active_threshold=0.22,     # arm considered "active" above this
        min_intent_threshold=0.18, # below this we assume no intent
        baseline_sec=15.0,         # learn initial "fresh" baseline over first seconds
        fatigue_trigger=0.75,      # threshold on fatigue_score to declare fatigued
    ):
        self.fps = fps
        self.N = int(window_sec * fps)
        self.active_thr = active_threshold
        self.intent_thr = min_intent_threshold

        self.baseline_frames = int(baseline_sec * fps)
        self._t = 0

        # ring buffers
        self.arm_hist = collections.deque(maxlen=self.N)
        self.intent_hist = collections.deque(maxlen=self.N)   # 1 if user likely intends to move
        self.active_hist = collections.deque(maxlen=self.N)   # 1 if arm above active_thr

        # learned baseline (fresh user)
        self.base_duty = None
        self.base_mean = None

        self.fatigue_score = 0.0
        self.fatigued = False
        self.fatigue_trigger = fatigue_trigger

    def update(self, arm_activation: float, move_intent: bool):
        """
        arm_activation: normalized 0..1
        move_intent: whether the player is trying to move (from your control logic)
        """
        self._t += 1

        arm = float(np.clip(arm_activation, 0.0, 1.0))
        intent = 1.0 if move_intent else 0.0

        active = 1.0 if arm >= self.active_thr else 0.0

        self.arm_hist.append(arm)
        self.intent_hist.append(intent)
        self.active_hist.append(active)

        # ---- build baseline during early "fresh" period ----
        if self._t == self.baseline_frames:
            self.base_duty = self._duty_cycle()
            self.base_mean = self._mean_arm_when_intent()
            # if user barely moved during baseline, keep safe defaults
            if self.base_duty is None: self.base_duty = 0.6
            if self.base_mean is None: self.base_mean = 0.35

        # Need enough history
        if len(self.arm_hist) < max(60, self.N // 4) or self.base_duty is None:
            self.fatigue_score = 0.0
            self.fatigued = False
            return self.fatigue_score, self.fatigued

        # ---- features ----
        duty = self._duty_cycle()                 # fraction of time active when intent
        mean_arm = self._mean_arm_when_intent()   # average activation during intent
        fail_rate = self._fail_rate()             # intent but not active

        # Normalize vs baseline
        duty_drop = np.clip((self.base_duty - duty) / max(1e-6, self.base_duty), 0.0, 1.0)
        mean_drop = np.clip((self.base_mean - mean_arm) / max(1e-6, self.base_mean), 0.0, 1.0)

        # Combine into fatigue score (0..1)
        # duty_drop captures "more sparse contractions"
        # mean_drop captures "can't reach same level"
        # fail_rate captures "tries but doesn't cross threshold"
        score = 0.45 * duty_drop + 0.35 * mean_drop + 0.20 * np.clip(fail_rate, 0.0, 1.0)

        # Smooth it so it doesn't flicker
        self.fatigue_score = 0.85 * self.fatigue_score + 0.15 * float(score)

        self.fatigued = self.fatigue_score >= self.fatigue_trigger
        return self.fatigue_score, self.fatigued

    def reset_after_rest(self):
        """Call after user rests; reduces fatigue and re-learns baseline slowly."""
        self.fatigue_score = max(0.0, self.fatigue_score * 0.3)
        self.fatigued = False
        # keep baseline; it represents that user's fresh control

    # ---------------- helpers ----------------
    def _duty_cycle(self):
        # duty cycle only meaningful when there is intent
        intent = np.array(self.intent_hist, dtype=np.float32)
        if intent.sum() < 10:  # too little intent in window
            return None
        active = np.array(self.active_hist, dtype=np.float32)
        # fraction of frames active among intent frames
        return float((active * intent).sum() / intent.sum())

    def _mean_arm_when_intent(self):
        intent = np.array(self.intent_hist, dtype=np.float32)
        if intent.sum() < 10:
            return None
        arm = np.array(self.arm_hist, dtype=np.float32)
        return float((arm * intent).sum() / intent.sum())

    def _fail_rate(self):
        # among intent frames: how often arm is below active threshold
        intent = np.array(self.intent_hist, dtype=np.float32)
        if intent.sum() < 10:
            return 0.0
        active = np.array(self.active_hist, dtype=np.float32)
        fails = (1.0 - active) * intent
        return float(fails.sum() / intent.sum())
    
    def end_of_session_fatigued(self, drop_trigger=0.35, min_baseline=0.30):
        if self.base_duty is None:
            return False

        duty = self._duty_cycle()
        if duty is None:
            return False

        # avoid triggering if baseline was too low (user wasn't really moving)
        if self.base_duty < min_baseline:
            return False

        duty_drop = (self.base_duty - duty) / max(1e-6, self.base_duty)
        return duty_drop >= drop_trigger

