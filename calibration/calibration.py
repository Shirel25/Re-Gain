class CalibrationResult:
    def __init__(self, baseline, max_activation):
        self.baseline = baseline
        self.max_activation = max_activation

# ======================================================================================================

class UserCalibration:
    """
    Store calibration parameters for one user session.
    """

    def __init__(self):
        self.arm = None
        self.leg = None
        self.control_params = ControlParameters()

    def set_arm_calibration(self, baseline, max_activation):
        self.arm = CalibrationResult(baseline, max_activation)

    def set_leg_calibration(self, baseline, max_activation):
        self.leg = CalibrationResult(baseline, max_activation)

    def is_complete(self):
        return self.arm is not None and self.leg is not None
    
# ======================================================================================================

class ControlParameters:
    """
    Control thresholds derived from user calibration.
    Values are expressed as ratios of normalized activation.
    """

    def __init__(self, theta_min=0.10, theta_low=0.10, theta_high=0.30):
        self.theta_min = theta_min
        self.theta_low = theta_low
        self.theta_high = theta_high

# ======================================================================================================

def fake_calibration():
    """
    Fake calibration used for development and testing.
    Values are normalized references, not absolute EMG values.
    """

    calibration = UserCalibration()

    # Example values based on observed EMG ranges
    # These represent baseline and max activation AFTER normalization
    calibration.set_arm_calibration(
        baseline=0.0,
        max_activation=1.0
    )

    calibration.set_leg_calibration(
        baseline=0.0,
        max_activation=1.0
    )

    return calibration

