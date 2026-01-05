import os
from natsort import natsorted
import shutil
import copy 
import time
from PyQt5.QtCore import Qt, QRectF, QSize, pyqtSlot,pyqtSignal
from PyQt5.QtGui import QPolygonF,QColor,QPainter
from PyQt5.QtWidgets import (QWidget, QApplication, QSizePolicy, QHBoxLayout, QVBoxLayout, 
                           QStackedWidget, QLabel, QMessageBox,QTextBrowser,QDialog)

from ...common.config import isDarkTheme
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.font import setFont
from ...common.color import autoFallbackThemeColor
from ...common.animation import FluentAnimation,FluentAnimationType,FluentAnimationProperty
from ...components.widgets.button import PushButton


class PivotItem(PushButton):

    itemClicked = pyqtSignal(bool)

    def _postInit(self):
        self.isSelected = False
        self.setProperty('isSelected', False)
        self.clicked.connect(lambda: self.itemClicked.emit(True))
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect) # 使布局使用小部件的矩形而不是其内容矩形

        FluentStyleSheet.PIVOT.apply(self)
        setFont(self, 14)

    def setSelected(self, isSelected: bool):
        if self.isSelected == isSelected:
            return

        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())
        self.update()


class Pivot(QWidget):

    currentItemChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = {}  
        self._currentRouteKey = None

        self.hBoxLayout = QHBoxLayout(self)
        self.slideAni = FluentAnimation.create(FluentAnimationType.POINT_TO_POINT, FluentAnimationProperty.SCALE, value=0, parent=self) # 指示器缩放动画

        FluentStyleSheet.PIVOT.apply(self)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setAlignment(Qt.AlignLeft)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def addItem(self, routeKey: str, text: str, onClick=None, icon=None):
        return self.insertItem(-1, routeKey, text, onClick, icon)

    def insertItem(self, index: int, routeKey: str, text: str, onClick=None, icon=None):
        if routeKey in self.items:
            return

        item = PivotItem(text, self)
        if icon:
            item.setIcon(icon)

        self.insertWidget(index, routeKey, item, onClick)
        
        return item

    def insertWidget(self, index: int, routeKey: str, widget: PivotItem, onClick=None):
       
        if routeKey in self.items:
            return

        widget.setProperty('routeKey', routeKey)
        widget.itemClicked.connect(self._onItemClicked)
        if onClick:
            widget.itemClicked.connect(onClick)

        self.items[routeKey] = widget
        self.hBoxLayout.insertWidget(index, widget, 1) # 插入到指定索引位置，权重为1

    def currentItem(self):
        if self._currentRouteKey is None:
            return None

        return self.widget(self._currentRouteKey)

    def currentRouteKey(self):
        return self._currentRouteKey

    def setCurrentItem(self, routeKey: str):
        """ 设置当前选中项 """
        if routeKey not in self.items or routeKey == self.currentRouteKey():
            return

        self._currentRouteKey = routeKey
        self.slideAni.startAnimation(self.widget(routeKey).x())

        for k, item in self.items.items():
            item.setSelected(k == routeKey)

        self.currentItemChanged.emit(routeKey)

    def showEvent(self, e):
        super().showEvent(e)
        self._adjustIndicatorPos()


    def _onItemClicked(self):
        item = self.sender()
        self.setCurrentItem(item.property('routeKey'))

    def widget(self, routeKey: str):
        if routeKey not in self.items:
            raise Exception(f"`{routeKey}` is illegal.")

        return self.items[routeKey]

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._adjustIndicatorPos()

    def _adjustIndicatorPos(self): # 调整指示器位置
        item = self.currentItem()
        if item:
            self.slideAni.stop()
            self.slideAni.setValue(item.x())

    def paintEvent(self, e):
        QWidget.paintEvent(self, e)

        if not self.currentItem():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 14))
            painter.setBrush(QColor(255, 255, 255, 15))
        else:
            painter.setPen(QColor(0, 0, 0, 19))
            painter.setBrush(QColor(255, 255, 255, 179))

        item = self.currentItem()
        rect = item.rect().adjusted(1, 1, -1, -1).translated(int(self.slideAni.value()), 0)
        painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(themeColor())

        x = int(self.currentItem().width() / 2 - 8 + self.slideAni.value())
        painter.drawRoundedRect(QRectF(x, self.height() - 3.5, 16, 3), 1.5, 1.5)


class SegmentedWidget(Pivot):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)



