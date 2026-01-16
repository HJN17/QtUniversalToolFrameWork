# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QScrollArea

from ...common.smooth_scroll import SmoothScroll, SmoothMode

from .scroll_bar import SmoothScrollBar, SmoothScrollDelegate

class ScrollArea(QScrollArea):
    """ 平滑滚动区域控件 """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scrollDelagate = SmoothScrollDelegate(self) # 创建平滑滚动委托实例，用于管理平滑滚动行为

    def setSmoothMode(self, mode: SmoothMode, orientation: Qt.Orientation):
        """ 设置平滑滚动模式    """
        if orientation == Qt.Orientation.Vertical:
            self.scrollDelagate.verticalSmoothScroll.setSmoothMode(mode)
        else:
            self.scrollDelagate.horizonSmoothScroll.setSmoothMode(mode)




class SingleDirectionScrollArea(QScrollArea):
    """ 单方向滚动区域控件 """

    def __init__(self, parent=None, orient=Qt.Vertical):
        
        super().__init__(parent)
        self.orient = orient
        self.smoothScroll = SmoothScroll(self, orient)  # 创建平滑滚动实例，指定当前控件和滚动方向
        self.vScrollBar = SmoothScrollBar(Qt.Vertical, self)    # 创建垂直平滑滚动条实例  
        self.hScrollBar = SmoothScrollBar(Qt.Horizontal, self)  # 创建水平平滑滚动条实例

    def setVerticalScrollBarPolicy(self, policy):
        super().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # 禁用垂直滚动条
        self.vScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff) # 强制隐藏垂直滚动条

    def setHorizontalScrollBarPolicy(self, policy):
        super().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setSmoothMode(self, mode):
        self.smoothScroll.setSmoothMode(mode)

    def keyPressEvent(self, e):
        if e.key() in [Qt.Key_Left, Qt.Key_Right]:
            # 如果是左右方向键，不处理该事件
            return
        return super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent):

        if e.angleDelta().x() != 0:
            return

        self.smoothScroll.wheelEvent(e)
        e.setAccepted(True)

