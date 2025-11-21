# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QAbstractScrollArea

from components.widgets.stacked_widget import PopUpAniStackedWidget


class StackedWidget(QFrame):
    """ 带动画效果的堆叠窗口部件，继承自QFrame
    用于管理多个子界面，支持平滑切换动画，通常与导航组件配合使用 """

    currentChanged = pyqtSignal(int)  # 当前显示页面索引变化时发射的信号，参数为新索引

    def __init__(self, parent=None):
        super().__init__(parent=parent)  # 调用父类QFrame的初始化方法，设置父部件
        self.hBoxLayout = QHBoxLayout(self)  # 创建水平布局管理器，用于管理当前部件内的控件排列
        self.view = PopUpAniStackedWidget(self)  # 初始化带弹出动画的堆叠窗口核心控件

        # 设置水平布局的外边距为0（上、右、下、左均为0），使内部控件贴边显示
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view)  # 将动画堆叠窗口控件添加到水平布局

        # 连接堆叠窗口的currentChanged信号到当前类的同名信号（转发信号）
        self.view.currentChanged.connect(self.currentChanged)
        self.setAttribute(Qt.WA_StyledBackground)  # 设置部件支持样式表背景绘制

    def isAnimationEnabled(self) -> bool:
        """ 判断是否启用切换动画
        :return: 布尔值，True表示启用动画，False表示禁用
        """
        return self.view.isAnimationEnabled  # 返回内部堆叠窗口的动画启用状态

    def setAnimationEnabled(self, isEnabled: bool):
        """ 设置是否启用切换动画
        :param isEnabled: 布尔值，True启用动画，False禁用动画
        """
        # 调用内部堆叠窗口的方法设置动画启用状态
        self.view.setAnimationEnabled(isEnabled)

    def addWidget(self, widget):
        """ 向堆叠窗口添加子部件
        :param widget: 要添加的QWidget子类实例
        """
        self.view.addWidget(widget)

    def removeWidget(self, widget):
        """ 从堆叠窗口移除子部件
        :param widget: 要移除的QWidget子类实例
        """
        self.view.removeWidget(widget)

    def widget(self, index: int):
        """ 获取指定索引位置的子部件
        :param index: 子部件的索引（从0开始）
        :return: 索引对应的QWidget实例，若索引无效则返回None
        """
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=True):
        """ 设置当前显示的子部件，并可指定切换动画效果
        :param widget: 要显示的目标子部件
        :param popOut: 布尔值，True表示使用弹出动画，False表示使用淡入淡出动画
        """
        # 如果目标部件是滚动区域（如QScrollArea），则将其垂直滚动条重置到顶部
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().setValue(0)

        if not popOut:
            # 不使用弹出动画时：调用内部堆叠窗口切换部件，动画持续时间500毫秒
            self.view.setCurrentWidget(widget, duration=200)
        else:
            # 使用弹出动画时：调用内部堆叠窗口切换部件，启用弹出效果，动画持续500毫秒，缓动曲线为InQuad（先慢后快）
            self.view.setCurrentWidget(
                widget, True, False, 200, QEasingCurve.InQuad)

    def setCurrentIndex(self, index, popOut=True):
        """ 通过索引设置当前显示的子部件
        :param index: 目标子部件的索引（从0开始）
        :param popOut: 布尔值，True使用弹出动画，False使用淡入淡出动画
        """
        # 调用setCurrentWidget方法，传入索引对应的部件
        self.setCurrentWidget(self.view.widget(index), popOut)

    def currentIndex(self):
        """ 获取当前显示子部件的索引
        :return: 整数，当前显示部件的索引（从0开始）
        """
        return self.view.currentIndex()

    def currentWidget(self):
        """ 获取当前显示的子部件
        :return: 当前显示的QWidget实例，若无则返回None
        """
        return self.view.currentWidget()

    def indexOf(self, widget):
        """ 获取指定子部件的索引
        :param widget: 目标子部件实例
        :return: 整数，部件的索引（从0开始）；若部件不在堆叠窗口中则返回-1
        """
        return self.view.indexOf(widget)

    def count(self):
        """ 获取堆叠窗口中子部件的总数
        :return: 整数，子部件的数量
        """
        return self.view.count()
    




