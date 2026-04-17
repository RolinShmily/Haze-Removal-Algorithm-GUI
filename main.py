"""
图像去雾系统
程序入口

使用方法:
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import core.dark_channel       
import core.guided_filter      
import core.retinex            
import core.clahe_dehaze       
import core.improved_dcp       
import core.paper_improved     

from ui.main_window import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    from ui.theme import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    main()
