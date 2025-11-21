# coding:utf-8
from typing import List
from PyQt5.QtCore import (QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation,
                          pyqtSignal)
from PyQt5.QtWidgets import QStackedWidget, QWidget

class PopUpAniInfo:
    """ 弹出动画信息数据类
    用于存储与弹出动画相关的部件、偏移量和动画对象信息
    """
    def __init__(self, widget: QWidget, deltaX: int, deltaY, ani: QPropertyAnimation):
        self.widget = widget  # 动画作用的目标部件
        self.deltaX = deltaX  # 动画X轴偏移量（起始位置与目标位置的水平差）
        self.deltaY = deltaY  # 动画Y轴偏移量（起始位置与目标位置的垂直差）
        self.ani = ani        # 控制该部件的属性动画对象（QPropertyAnimation）


class PopUpAniStackedWidget(QStackedWidget):
    """ 带有弹出动画效果的堆叠窗口部件
    继承自QStackedWidget，支持页面切换时的弹出/收起动画效果，可配置偏移量和缓动曲线
    """

    aniFinished = pyqtSignal()  # 动画结束时发射的信号
    aniStart = pyqtSignal()     # 动画开始时发射的信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []    # 存储每个部件的动画信息列表（元素类型为PopUpAniInfo）
        self.isAnimationEnabled = True  # 是否启用动画的开关（布尔值）
        self._nextIndex = None   # 私有变量，存储下一个要切换到的页面索引
        self._ani = None    # 私有变量，存储当前正在执行的动画对象

    def addWidget(self, widget, deltaX=0, deltaY=70):
        """ 添加部件到堆叠窗口，并配置动画偏移量

        Parameters
        -----------
        widget: QWidget
            要添加的目标部件

        deltaX: int
            动画从起始位置到结束位置的X轴偏移量（像素）

        deltaY: int
            动画从起始位置到结束位置的Y轴偏移量（像素）
        """
        super().addWidget(widget)

        # 创建PopUpAniInfo对象，存储部件、偏移量和动画对象，添加到aniInfos列表
        self.aniInfos.append(PopUpAniInfo(
            widget=widget,
            deltaX=deltaX,
            deltaY=deltaY,
            ani=QPropertyAnimation(widget, b'pos'),  # 动画作用于部件的'pos'（位置）属性
        ))

    def removeWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index == -1:
            return
        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setAnimationEnabled(self, isEnabled: bool):
        """ 设置是否启用弹出动画

        Parameters
        ----------
        isEnabled: bool
            True表示启用动画，False表示禁用动画
        """
        self.isAnimationEnabled = isEnabled

    def setCurrentIndex(self, index: int, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                        duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """ 设置当前显示的页面索引，并执行弹出/收起动画

        Parameters
        ----------
        index: int
            要显示的目标页面索引

        needPopOut: bool
            True表示当前页面执行"弹出"（移出）动画，False表示目标页面执行"弹入"（移入）动画

        showNextWidgetDirectly: bool
            动画开始时是否直接显示下一个页面（True表示立即显示，False表示动画结束后显示）

        duration: int
            动画持续时间（毫秒）

        easingCurve: QEasingCurve
            动画缓动曲线（控制动画速度变化规律，如QEasingCurve.OutQuad表示先快后慢）
        """
        # 如果目标索引超出有效范围（小于0或大于等于部件总数），直接返回
        if index < 0 or index >= self.count():
            return

        # 如果目标索引与当前索引相同，直接返回（无需切换）
        if index == self.currentIndex():
            return

        # 如果禁用动画，直接调用父类方法设置当前索引
        if not self.isAnimationEnabled:
            return super().setCurrentIndex(index)

        # 如果当前有动画正在运行，停止该动画并触发动画结束处理
        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        # 记录下一个要切换到的页面索引
        self._nextIndex = index

        # 获取目标页面和当前页面的动画信息对象
        nextAniInfo = self.aniInfos[index]
        currentAniInfo = self.aniInfos[self.currentIndex()]

        # 获取当前显示的部件和目标部件
        currentWidget = self.currentWidget()
        nextWidget = nextAniInfo.widget
        # 根据needPopOut选择动画对象：弹出动画使用当前页面的动画，弹入动画使用目标页面的动画
        ani = currentAniInfo.ani if needPopOut else nextAniInfo.ani
        # 记录当前执行的动画对象
        self._ani = ani

        if needPopOut:
            # 弹出动画：获取当前页面的偏移量
            deltaX, deltaY = currentAniInfo.deltaX, currentAniInfo.deltaY
            # 计算动画结束位置（当前位置 + 偏移量，即部件移出屏幕的位置）
            pos = currentWidget.pos() + QPoint(deltaX, deltaY)
            # 配置动画：从当前位置移动到结束位置
            self.__setAnimation(ani, currentWidget.pos(), pos, duration, easingCurve)
            # 根据参数决定是否立即显示目标页面
            nextWidget.setVisible(showNextWidgetDirectly)
        else:
            # 弹入动画：获取目标页面的偏移量
            deltaX, deltaY = nextAniInfo.deltaX, nextAniInfo.deltaY
            # 计算动画起始位置（目标部件初始位置 + 偏移量，即部件从屏幕外进入的位置）
            pos = nextWidget.pos() + QPoint(deltaX, deltaY)
            # 配置动画：从起始位置移动到目标位置（目标部件的原始x坐标，y=0）
            self.__setAnimation(ani, pos, QPoint(nextWidget.x(), 0), duration, easingCurve)
            # 直接调用父类方法设置当前索引为目标索引（显示目标部件，后续执行弹入动画）
            super().setCurrentIndex(index)

        # 连接动画结束信号到__onAniFinished槽函数
        ani.finished.connect(self.__onAniFinished)
        # 启动动画
        ani.start()
        # 发射动画开始信号
        self.aniStart.emit()

    def setCurrentWidget(self, widget, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                         duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """ 设置当前显示的部件，并执行弹出/收起动画

        Parameters
        ----------
        widget: QWidget
            要显示的目标部件

        needPopOut: bool
            True表示当前页面执行"弹出"（移出）动画，False表示目标页面执行"弹入"（移入）动画

        showNextWidgetDirectly: bool
            动画开始时是否直接显示下一个页面（True表示立即显示，False表示动画结束后显示）

        duration: int
            动画持续时间（毫秒）

        easingCurve: QEasingCurve
            动画缓动曲线（控制动画速度变化规律，如QEasingCurve.OutQuad表示先快后慢）
        """
        # 通过部件获取索引，调用setCurrentIndex切换页面并执行动画
        self.setCurrentIndex(
            self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __setAnimation(self, ani, startValue, endValue, duration, easingCurve=QEasingCurve.Linear):
        """ 配置动画的参数（内部辅助方法）

        Parameters
        ----------
        ani: QPropertyAnimation
            要配置的动画对象

        startValue: QPoint
            动画起始位置

        endValue: QPoint
            动画结束位置

        duration: int
            动画持续时间（毫秒）

        easingCurve: QEasingCurve
            动画缓动曲线（默认值为线性变化）
        """
        # 设置动画的缓动曲线
        ani.setEasingCurve(easingCurve)
        # 设置动画的起始值（位置）
        ani.setStartValue(startValue)
        # 设置动画的结束值（位置）
        ani.setEndValue(endValue)
        # 设置动画的持续时间
        ani.setDuration(duration)

    def __onAniFinished(self):
        """ 动画结束时的槽函数 """
        self._ani.disconnect() #
        # 调用父类方法设置当前索引为_nextIndex（确保状态同步）
        super().setCurrentIndex(self._nextIndex)
        # 发射动画结束信号
        self.aniFinished.emit()
