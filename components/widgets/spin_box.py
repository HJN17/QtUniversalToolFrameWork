# coding:utf-8
from enum import Enum

from PyQt5.QtCore import Qt, QSize, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPainterPath, QColor
from PyQt5.QtWidgets import (QSpinBox, QDoubleSpinBox, QToolButton, QHBoxLayout,
                             QDateEdit, QDateTimeEdit, QTimeEdit, QVBoxLayout, QApplication)

from common.style_sheet import FluentStyleSheet, themeColor, isDarkTheme
from common.icon import FluentIconBase, Theme, getIconColor
from common.font import setFont
from common.color import FluentSystemColor, autoFallbackThemeColor
from .button import TransparentToolButton
from .line_edit import LineEditMenu
from .flyout import Flyout, FlyoutViewBase, FlyoutAnimationType


class SpinIcon(FluentIconBase, Enum):
    """ Spin icon """

    UP = "Up"
    DOWN = "Down"

    def path(self, theme=Theme.AUTO):
        return f':/resource/images/spin_box/{self.value}_{getIconColor(theme)}.svg'



class SpinButton(QToolButton):

    def __init__(self, icon: SpinIcon, parent=None):
        super().__init__(parent=parent)
        self.isPressed = False
        self._icon = icon
        self.setFixedSize(31, 23)
        self.setIconSize(QSize(10, 10))
        FluentStyleSheet.SPIN_BOX.apply(self)

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.36)
        elif self.isPressed:
            painter.setOpacity(0.7)

        self._icon.render(painter, QRectF(10, 6.5, 11, 11))

class SpinBoxBase:
    """ Spin box ui """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isError = False
        self.lightFocusedBorderColor = QColor()
        self.darkFocusedBorderColor = QColor()

        self.hBoxLayout = QHBoxLayout(self)

        self.setProperty('transparent', True)
        FluentStyleSheet.SPIN_BOX.apply(self)
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.setFixedHeight(33)
        setFont(self)

        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)

    def isError(self):
        return self._isError

    def setError(self, isError: bool):
        """ set the error status """
        if isError == self.isError():
            return

        self._isError = isError
        self.update()

    def setReadOnly(self, isReadOnly: bool):
        super().setReadOnly(isReadOnly)
        self.setSymbolVisible(not isReadOnly)

    def setSymbolVisible(self, isVisible: bool):
        """ set whether the spin symbol is visible """
        self.setProperty("symbolVisible", isVisible)
        self.setStyle(QApplication.style())

    def setCustomFocusedBorderColor(self, light, dark):
        """ set the border color in focused status

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            border color in light/dark theme mode
        """
        self.lightFocusedBorderColor = QColor(light)
        self.darkFocusedBorderColor = QColor(dark)
        self.update()

    def focusedBorderColor(self):
        if self.isError():
            return FluentSystemColor.CRITICAL_FOREGROUND.color()

        return autoFallbackThemeColor(self.lightFocusedBorderColor, self.darkFocusedBorderColor)

    def _showContextMenu(self, pos):
        menu = LineEditMenu(self.lineEdit())
        menu.exec_(self.mapToGlobal(pos))

    def _drawBorderBottom(self):
        if not self.hasFocus():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.addRoundedRect(QRectF(0, h-10, w, 10), 5, 5)

        rectPath = QPainterPath()
        rectPath.addRect(0, h-10, w, 8)
        path = path.subtracted(rectPath)

        painter.fillPath(path, self.focusedBorderColor())

    def paintEvent(self, e):
        super().paintEvent(e)
        self._drawBorderBottom()


class InlineSpinBoxBase(SpinBoxBase):
    """ Inline spin box base """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.upButton = SpinButton(SpinIcon.UP, self)
        self.downButton = SpinButton(SpinIcon.DOWN, self)

        self.hBoxLayout.setContentsMargins(0, 4, 4, 4)
        self.hBoxLayout.setSpacing(5)
        self.hBoxLayout.addWidget(self.upButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.downButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.upButton.clicked.connect(self.stepUp)
        self.downButton.clicked.connect(self.stepDown)

    def setSymbolVisible(self, isVisible: bool):
        super().setSymbolVisible(isVisible)
        self.upButton.setVisible(isVisible)
        self.downButton.setVisible(isVisible)

    def setAccelerated(self, on: bool):
        super().setAccelerated(on)
        self.upButton.setAutoRepeat(on)
        self.downButton.setAutoRepeat(on)

class SpinBox(InlineSpinBoxBase, QSpinBox):
    """ Spin box """

class DoubleSpinBox(InlineSpinBoxBase, QDoubleSpinBox):
    """ Double spin box """


class TimeEdit(InlineSpinBoxBase, QTimeEdit):
    """ Time edit """


class DateTimeEdit(InlineSpinBoxBase, QDateTimeEdit):
    """ Date time edit """



class DateEdit(InlineSpinBoxBase, QDateEdit):
    """ Date edit """

