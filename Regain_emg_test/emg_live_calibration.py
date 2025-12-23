from bitalino import BITalino
import numpy as np
import time

# =========================
# Configuration
# =========================

MAC_ADDRESS = "20:18:08:08:02:30"
EMG_CHANNEL = 1      
SAMPLING_RATE = 1000
WINDOW_SIZE = 300
GAIN = 10

# =========================
# Connection
# =========================

device = BITalino(MAC_ADDRESS)
device.start(SAMPLING_RATE, [EMG_CHANNEL])

data = device.read(WINDOW_SIZE)
print("Shape:", data.shape)
print("First row:", data[0])

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

def record_phase(device, duration, label):
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

        emg = data[:, 5]                 # A5 (EMG)
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
# Calibration protocol
# =========================

# Repos → baseline
activation_rest = record_phase(device, 10, "Repos (muscle relâché)")
baseline = np.mean(activation_rest)

print(f"\nBaseline (repos): {baseline:.2f}")

# Contraction modérée
activation_mod = record_phase(device, 12, "Contraction modérée")
activation_mod_corr = np.maximum(0, activation_mod - baseline)

# Contraction forte
activation_max = record_phase(device, 6, "Contraction forte")
activation_max_corr = np.maximum(0, activation_max - baseline)

# =========================
# Results
# =========================

print("\nCalibration terminée (après tare)")
print(f"Modérée (mean) : {np.mean(activation_mod_corr):.2f}")
print(f"Forte   (max)  : {np.max(activation_max_corr):.2f}")

print("\nNormalisation possible :")
print("Activation_norm = (activation - baseline) / max_activation")

device.stop()
device.close()
