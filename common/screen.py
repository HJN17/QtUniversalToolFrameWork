from PyQt5.QtCore import QRect  # 导入Qt核心模块中的坐标点和矩形区域类
from PyQt5.QtGui import QCursor  # 导入Qt GUI模块中的光标类
from PyQt5.QtWidgets import QApplication  # 导入Qt窗口部件模块中的应用程序类


def getCurrentScreen():
    """
    获取当前光标所在的屏幕对象
    
    功能说明：通过判断当前鼠标光标位置，确定其所在的屏幕设备，返回对应的屏幕对象。
    当光标不在任何屏幕区域内时（罕见情况），返回None。
    
    返回值：
        QScreen or None: 光标所在的屏幕对象，若未找到则返回None
    """
    cursorPos = QCursor.pos() 
    
   
    for s in QApplication.screens():
    
        if s.geometry().contains(cursorPos):
            return s 

    return None 

def getCurrentScreenGeometry(avaliable=True):
    """
    获取当前屏幕的几何区域（支持获取可用区域或完整区域）
    
    功能说明：获取当前光标所在屏幕的几何尺寸信息，可选择返回可用区域（排除任务栏等系统区域）
    或完整屏幕区域。当无法获取屏幕信息时，返回默认分辨率(1920x1080)的矩形区域。
    
    参数：
        avaliable (bool): 可选参数，默认为True。
                          - True: 返回屏幕的可用区域（排除任务栏等系统保留区域）
                          - False: 返回屏幕的完整几何区域（包含所有像素）
    
    返回值：
        QRect: 屏幕的几何区域对象，包含x,y坐标及宽度、高度信息
    """
    screen = getCurrentScreen() or QApplication.primaryScreen()

    if not screen:
        return QRect(0, 0, 1920, 1080)

    return screen.availableGeometry() if avaliable else screen.geometry()