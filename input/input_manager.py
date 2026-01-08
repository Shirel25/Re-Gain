from input.keyboard import KeyboardInput


class InputManager:
    def __init__(self, mode="keyboard"):
        self.mode = mode

        if self.mode == "keyboard":
            self.input = KeyboardInput()
        else:
            raise ValueError("Unknown input mode")

    def update(self, events):
        self.input.update(events)

    def jump_pressed(self):
        return self.input.jump_pressed()
    
    def move_right_pressed(self):
        return self.input.move_right_pressed()

