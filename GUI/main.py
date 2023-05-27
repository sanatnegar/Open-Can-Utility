import sys
from Dialog import *


def main():
    app = QApplication(sys.argv)
    dialog = Dialog()
    dialog.show()
    app.exec_()


if __name__ == '__main__':
    main()
