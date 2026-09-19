import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader

class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        loader = QUiLoader()
        self.window = loader.load("design.ui")
        self.window.helloBtn.clicked.connect(self.print_hello)

    def print_hello(self):
        print("Hello World")

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApplication()
    main_app.run()