import sys

from PyQt6.QtWidgets import QApplication

from dashboard.lock_screen import LockScreen
from dashboard.desktop import Desktop


class FridayApplication:

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.lock_screen = None
        self.desktop = None

    def start(self):

        self.show_lock_screen()

        return self.app.exec()

    def show_lock_screen(self):

        self.lock_screen = LockScreen()

        self.lock_screen.authenticated_signal.connect(
            self.authentication_success
        )

        self.lock_screen.showFullScreen()

    def authentication_success(self, username):

        print()
        print("=" * 50)
        print("FRIDAY AUTHENTICATION SUCCESSFUL")
        print(f"USER: {username}")
        print("=" * 50)
        print()

        # Close the login screen after successful authentication
        self.lock_screen.close()

        self.show_desktop(username)

    def show_desktop(self, username):

        self.desktop = Desktop(
            username
        )

        self.desktop.showFullScreen()

    def quit_application(self):

        if self.desktop:

            self.desktop.close()

        if self.lock_screen:

            self.lock_screen.close()

        self.app.quit()


def main():

    friday = FridayApplication()

    sys.exit(
        friday.start()
    )


if __name__ == "__main__":

    main()