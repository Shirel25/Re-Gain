from input.keyboard import KeyboardInput
from config import MAC_ADDRESS, EMG_BASELINE, EMG_MAX_ACTIVATION
from input.fake_emg import FakeEMGInput
from input.emg import EMGInput, DualEMGInput


class InputManager:
    def __init__(self, mode="keyboard", calibration=None, device=None):
        self.mode = mode
        self.calibration = calibration
        self.device = device

        if self.mode == "keyboard":
            self.input = KeyboardInput()
        
        elif self.mode == "emg":
            self.input = EMGInput(
                mac_address=MAC_ADDRESS,
                baseline=EMG_BASELINE,
                max_activation=EMG_MAX_ACTIVATION
            )

        elif self.mode == "fake_emg":
            self.input = FakeEMGInput()
    
        elif self.mode == "dual_emg":
            self.input = DualEMGInput(
                    device=self.device,
                    arm_channel=5,  # A5
                    leg_channel=2,  # A2
                    calibration=calibration
                )

        else:
            raise ValueError("Unknown input mode")

    def update(self, events):
        if self.mode == "keyboard":
            self.input.update(events)
            
        elif self.mode in ["emg", "fake_emg", "dual_emg"]:
            self.input.update()

    def jump_pressed(self):
        return self.input.jump_pressed()
    
    def move_right_pressed(self):
        return self.input.move_right_pressed()

