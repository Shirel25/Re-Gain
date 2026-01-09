from input.keyboard import KeyboardInput
from config import EMG_BASELINE, EMG_MAX_ACTIVATION
from input.fake_emg import FakeEMGInput
from input.emg import EMGInput


class InputManager:
    def __init__(self, mode="keyboard", calibration=None):
        self.mode = mode
        self.calibration = calibration

        if self.mode == "keyboard":
            self.input = KeyboardInput()
        
        elif self.mode == "emg":
            self.input = EMGInput(
                mac_address="20:18:08:08:02:30",
                baseline=EMG_BASELINE,
                max_activation=EMG_MAX_ACTIVATION
            )

        elif self.mode == "fake_emg":
            self.input = FakeEMGInput()
    
        else:
            raise ValueError("Unknown input mode")

    def update(self, events):
        if self.mode == "keyboard":
            self.input.update(events)
            
        elif self.mode in ["emg", "fake_emg"]:
            self.input.update()

    def jump_pressed(self):
        return self.input.jump_pressed()
    
    def move_right_pressed(self):
        return self.input.move_right_pressed()

