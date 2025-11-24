# coding: utf-8 
from enum import Enum
from PyQt5.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, pyqtSignal, QPoint, QPointF,pyqtProperty
from PyQt5.QtGui import QMouseEvent, QEnterEvent, QColor
from PyQt5.QtWidgets import QWidget, QLineEdit, QGraphicsDropShadowEffect

from .config import qconfig



class AnimationBase(QObject):
    """ 动画基类 """
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        parent.installEventFilter(self)

    def _onHover(self, e: QEnterEvent):
        pass  # 鼠标悬停事件处理方法

    def _onLeave(self, e: QEvent):
        pass  # 鼠标离开事件处理方法

    def _onPress(self, e: QMouseEvent):
        pass  # 鼠标按下事件处理方法

    def _onRelease(self, e: QMouseEvent):
        pass  # 鼠标释放事件处理方法

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            if e.type() == QEvent.MouseButtonPress:
                self._onPress(e)
            elif e.type() == QEvent.MouseButtonRelease: 
                self._onRelease(e)
            elif e.type() == QEvent.Enter:
                self._onHover(e)
            elif e.type() == QEvent.Leave:
                self._onLeave(e)

        return super().eventFilter(obj, e)

class TranslateYAnimation(AnimationBase): 
    """ 垂直平移动画类 """

    def __init__(self, parent: QWidget, offset=2):
        super().__init__(parent)
        self._y = 0
        self.maxOffset = offset
        self.ani = QPropertyAnimation(self, b'y', self) # 创建垂直平移动画对象，目标属性为'y'，目标对象为当前实例self

    @pyqtProperty(float)
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y 
        self.parent().update()
       
    def _onPress(self, e):
        self.ani.setEndValue(self.maxOffset)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)  # 设置缓动曲线为OutQuad（先快后慢）
        self.ani.setDuration(150)
        self.ani.start()

    def _onRelease(self, e):
        """ 释放事件处理方法 """
        self.ani.setEndValue(0)
        self.ani.setDuration(500) 
        self.ani.setEasingCurve(QEasingCurve.OutElastic) # 设置缓动曲线为OutElastic（弹性效果）
        self.ani.start()

class BackgroundAnimation:
    """ 背景动画部件类 """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.isHover = False 
        self.isPressed = False  
        self.bgColorObject = BackgroundColorObject(self)
        self.backgroundColorAni = QPropertyAnimation(self.bgColorObject, b'backgroundColor', self)
        self.backgroundColorAni.setDuration(500)
        self.installEventFilter(self)

        qconfig.themeChanged.connect(self._updateBackgroundColor) 

    def eventFilter(self, obj, e):
        if obj is self:
            if e.type() == QEvent.Type.EnabledChange:  # 若事件为部件启用状态变化事件
                if self.isEnabled():  # 若部件当前已启用
                    self.setBackgroundColor(self._normalBackgroundColor())
                else:
                    self.setBackgroundColor(self._disabledBackgroundColor())

        return super().eventFilter(obj, e) 

    def mousePressEvent(self, e):
        self.isPressed = True
        self._updateBackgroundColor()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self._updateBackgroundColor()
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self._updateBackgroundColor()

    def leaveEvent(self, e):
        self.isHover = False 
        self._updateBackgroundColor() 

    def focusInEvent(self, e):
        super().focusInEvent(e) 
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _focusInBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _disabledBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _updateBackgroundColor(self):
        if not self.isEnabled():
            color = self._disabledBackgroundColor()
        elif isinstance(self, QLineEdit) and self.hasFocus():
            color = self._focusInBackgroundColor() 
        elif self.isPressed:
            color = self._pressedBackgroundColor()  
        elif self.isHover: 
            color = self._hoverBackgroundColor()  
        else: 
            color = self._normalBackgroundColor()

        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color) 
        self.backgroundColorAni.start()

    def getBackgroundColor(self):
        return self.bgColorObject.backgroundColor

    def setBackgroundColor(self, color: QColor):
        self.bgColorObject.backgroundColor = color 

    @property
    def backgroundColor(self):
        return self.getBackgroundColor() 

class BackgroundColorObject(QObject): 
    """ 背景色对象类 """

    def __init__(self, parent: BackgroundAnimation):
        super().__init__(parent)
        self._backgroundColor = parent._normalBackgroundColor()

    @pyqtProperty(QColor) 
    def backgroundColor(self):
        return self._backgroundColor

    @backgroundColor.setter 
    def backgroundColor(self, color: QColor):
        self._backgroundColor = color 
        self.parent().update()
