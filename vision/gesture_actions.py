import pyautogui

TRACKING_REGION = (0.14, 0.86, 0.14, 0.86)


class GestureActionController:

    def __init__(self):

        self.screen_width, self.screen_height = (
            pyautogui.size()
        )

        self.previous_x = None
        self.previous_y = None

        self.smoothing = 0.28
        self.cursor_deadzone = 3
        self.last_emitted_x = None
        self.last_emitted_y = None

        self.was_pinching = False

        # Keep the emergency PyAutoGUI corner failsafe from
        # stopping FRIDAY when the cursor is intentionally moved
        # to a screen corner.
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

        # The hand does not need to leave the camera frame to
        # reach the edges of the screen.
        (
            self.camera_left_margin,
            self.camera_right_margin,
            self.camera_top_margin,
            self.camera_bottom_margin
        ) = TRACKING_REGION

    def map_axis(self, value, lower, upper):

        if value <= lower:
            return 0.0

        if value >= upper:
            return 1.0

        return (
            value - lower
        ) / (
            upper - lower
        )

    def move_cursor(self, x, y):

        screen_x = self.map_axis(
            x,
            self.camera_left_margin,
            self.camera_right_margin
        )

        screen_y = self.map_axis(
            y,
            self.camera_top_margin,
            self.camera_bottom_margin
        )

        target_x = int(
            screen_x * (self.screen_width - 1)
        )

        target_y = int(
            screen_y * (self.screen_height - 1)
        )

        if self.previous_x is None:

            self.previous_x = target_x
            self.previous_y = target_y

        else:

            self.previous_x = (
                self.previous_x * (1 - self.smoothing)
                + target_x * self.smoothing
            )

            self.previous_y = (
                self.previous_y * (1 - self.smoothing)
                + target_y * self.smoothing
            )

        cursor_x = int(self.previous_x)
        cursor_y = int(self.previous_y)

        if self.last_emitted_x is not None:
            movement_squared = (
                (cursor_x - self.last_emitted_x) ** 2
                + (cursor_y - self.last_emitted_y) ** 2
            )
            if movement_squared < self.cursor_deadzone ** 2:
                return

        self.last_emitted_x = cursor_x
        self.last_emitted_y = cursor_y

        pyautogui.moveTo(
            cursor_x,
            cursor_y,
            duration=0
        )

    def select(self):

        if not self.was_pinching:

            pyautogui.click()

            self.was_pinching = True

    def release_selection(self):

        self.was_pinching = False

    def reset(self):

        self.previous_x = None
        self.previous_y = None
        self.last_emitted_x = None
        self.last_emitted_y = None

        self.was_pinching = False

    def execute(
        self,
        gesture,
        index_tip=None
    ):

        if gesture == "POINT":

            self.release_selection()

            if index_tip is not None:

                self.move_cursor(
                    index_tip.x,
                    index_tip.y
                )

        elif gesture == "PINCH":

            self.select()

        else:

            self.release_selection()
