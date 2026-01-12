from bitalino import BITalino
import numpy as np
import time

from calibration.calibration import UserCalibration, MuscleCalibration

# =========================
# Configuration
# =========================

MAC_ADDRESS = "20:18:08:08:02:30"
ARM_CHANNEL = 5   # A5
LEG_CHANNEL = 2   # A2
SAMPLING_RATE = 1000
WINDOW_SIZE = 300
GAIN = 10


# =========================
# Utils
# =========================

def countdown(seconds):
    for i in range(seconds, 0, -1):
        print(i)
        time.sleep(1)

# =========================
# Recording function
# =========================

def record_phase(device, channel, duration, label, muscle_name):
    print(f"\n{label}")
    print("Prépare-toi...")
    countdown(3)
    print("ENREGISTREMENT")

    activation_values = []
    start = time.time()

    activation_prev = 0.0
    alpha = 0.8

    while time.time() - start < duration:
        data = device.read(WINDOW_SIZE)

        # emg = data[:, channel]                 # A5, A2 (EMG)
        
        
        # Les canaux analogiques sont toujours à la fin du tableau de données BITalino.
        # Si device.start(..., [A5, A2]), alors data[:, -2] = A5, data[:, -1] = A2
        if channel == ARM_CHANNEL:
            emg = data[:, -2] # A5
        elif channel == LEG_CHANNEL:
            emg = data[:, -1] # A2

        emg = emg - np.mean(emg)        # suppression offset DC

        emg_rect = np.abs(emg)
        envelope = np.mean(emg_rect)

        activation = envelope * GAIN
        

        activation_smooth = alpha * activation_prev + (1 - alpha) * activation
        activation_prev = activation_smooth

        activation_values.append(activation_smooth)

        print(f"Activation (smooth): {activation_smooth:.2f}")


    return np.array(activation_values)


# =========================
# Calibration muscle
# =========================
def calibrate_muscle(device, channel, muscle_name):
    print(f"\n==============================")
    print(f"CALIBRATION {muscle_name.upper()}")
    print(f"==============================")

    # -------------------------
    # Repos → baseline
    # -------------------------
    activation_rest = record_phase(
        device, channel, 10, "Repos (muscle relâché)", muscle_name
    )
    baseline = np.mean(activation_rest)

    print(f"{muscle_name} baseline : {baseline:.2f}")

    # -------------------------
    # Contraction modérée (info)
    # -------------------------
    activation_mod = record_phase(
        device, channel, 12, "Contraction modérée", muscle_name
    )
    activation_mod_corr = np.maximum(0, activation_mod - baseline)
    mod_mean = np.mean(activation_mod_corr)

    print(f"{muscle_name} modérée (mean) : {mod_mean:.2f}")

    # -------------------------
    # Contraction forte → max
    # -------------------------
    activation_max = record_phase(
        device, channel, 6, "Contraction forte", muscle_name
    )
    activation_max_corr = np.maximum(0, activation_max - baseline)
    max_activation = np.max(activation_max_corr)

    print(f"{muscle_name} forte (max)     : {max_activation:.2f}")

    return {
        "baseline": baseline,
        "mod_mean": mod_mean,
        "max_activation": max_activation
    }


# =========================
# MAIN CALIBRATION
# =========================

def real_calibration():
    device = BITalino(MAC_ADDRESS)
    device.start(SAMPLING_RATE, [ARM_CHANNEL, LEG_CHANNEL])

    calibration = UserCalibration()

    # ---- ARM ----
    arm = calibrate_muscle(device, ARM_CHANNEL, "Arm")
    calibration.arm = MuscleCalibration(
        baseline=arm["baseline"],
        max_activation=arm["max_activation"],
        mod_mean=arm["mod_mean"]
    )


    # ---- LEG ----
    leg = calibrate_muscle(device, LEG_CHANNEL, "Leg")
    calibration.leg = MuscleCalibration(
        baseline=leg["baseline"],
        max_activation=leg["max_activation"],
        mod_mean=leg["mod_mean"]
    )


    device.stop()
    device.close()

    print("\nCalibration complète ✔")
    return calibration


if __name__ == "__main__":
    real_calibration()


