# coding:utf-8

from typing import Union
from PyQt5.QtCore import pyqtProperty,QRect
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QWidget
from common.icon import FluentIconBase, drawIcon, toQIcon
from common.overload import singledispatchmethod


class IconWidget(QWidget):
    """ 
    图标显示部件：用于在界面中展示各种类型的图标（支持QIcon、资源路径字符串、FluentIconBase枚举）
    
    核心功能：
    - 支持多类型图标输入（QIcon对象、图标资源路径、FluentIconBase枚举成员）
    - 自动处理图标绘制逻辑（通过drawIcon函数实现跨类型统一渲染）
    - 提供Qt属性接口（icon属性），支持信号-槽机制动态更新图标
    
    构造函数重载：
    1. IconWidget(parent: QWidget = None) - 无图标初始化，需后续通过setIcon设置
    2. IconWidget(icon: QIcon | str | FluentIconBase, parent: QWidget = None) - 带图标初始化
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon())

  
    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        # 调用无图标构造函数初始化父部件和基础属性
        self.__init__(parent)
        # 设置FluentIconBase类型图标
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        # 调用无图标构造函数初始化父部件和基础属性
        self.__init__(parent)
        # 设置QIcon类型图标
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        # 调用无图标构造函数初始化父部件和基础属性
        self.__init__(parent)
        # 设置字符串路径类型图标
        self.setIcon(icon)

    def getIcon(self):
        """ 
        获取当前图标（QIcon类型）
        
        返回:
            QIcon - 转换后的Qt标准图标对象（通过toQIcon处理内部_icon得到）
        """
        return toQIcon(self._icon)

    def setIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        self._icon = icon
        self.update()

    def paintEvent(self, e):
        """ 
        重写QWidget的绘制事件：实现图标在部件内的渲染
        
        参数:
            e: QPaintEvent - 绘制事件对象（包含绘制区域等信息，此处未直接使用）
        """
        # 创建QPainter对象，关联当前部件作为绘制目标
        painter = QPainter(self)
        # 设置绘制渲染提示：启用抗锯齿（使图标边缘平滑）和平滑图像变换（缩放/旋转无模糊）
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    
        drawIcon(self._icon, painter, self.rect())

    # 将icon定义为Qt属性：通过getIcon获取，setIcon设置，支持在Qt Designer中编辑和信号绑定
    icon = pyqtProperty(QIcon, getIcon, setIcon)