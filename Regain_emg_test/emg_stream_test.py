"""
emg_stream_test.py

Minimal prototype for EMG signal acquisition using BITalino.
This script is used to validate the acquisition pipeline before
implementing user modeling and adaptive game mechanics.

"""

from bitalino import BITalino
import time
import numpy as np

# BITalino Bluetooth MAC address
MAC_ADDRESS = "20:18:08:08:02:30"

# EMG channel (A1)
ANALOG_CHANNELS = [0]

# Sampling rate (Hz)
SAMPLING_RATE = 1000

def main():
    print("Connecting to BITalino...")
    device = BITalino(MAC_ADDRESS)

    print("Starting acquisition...")
    device.start(SAMPLING_RATE, ANALOG_CHANNELS)

    time.sleep(2)

    print("Reading EMG data...")
    data = device.read(100)  # Read 100 samples
    emg_signal = data[:, -1]

    print("Raw EMG samples:")
    print(emg_signal)

    print("Stopping acquisition.")
    device.stop()
    device.close()

if __name__ == "__main__":
    main()
