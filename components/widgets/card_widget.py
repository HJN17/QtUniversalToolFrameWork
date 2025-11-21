# coding:utf-8
from typing import List, Union
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, pyqtProperty, QPropertyAnimation, QPoint, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel

from common.overload import singledispatchmethod
from common.style_sheet import isDarkTheme, FluentStyleSheet
from common.animation import BackgroundAnimation
from common.font import setFont
from common.icon import FluentIconBase
from components.widgets.label import BodyLabel, CaptionLabel
from components.widgets.icon_widget import IconWidget

class CardWidget(BackgroundAnimation, QFrame):
    """ 
    卡片组件基类：继承自背景动画部件和框架部件，提供基础卡片样式和交互效果。
    支持悬停、按下状态的背景色和边框变化，可自定义圆角半径，内置点击信号。
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isClickEnabled = False
        self._borderRadius = 15

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setClickEnabled(self, isEnabled: bool):
        self._isClickEnabled = isEnabled
        self.update()

    def isClickEnabled(self):
        # 获取点击启用状态：返回当前标志值
        return self._isClickEnabled

    def _normalBackgroundColor(self):
        # 正常状态背景色：根据主题返回不同透明度的白色
        # 深色主题：白色，透明度13/255；浅色主题：白色，透明度170/255
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        # 悬停状态背景色：根据主题返回不同透明度的白色
        # 深色主题：白色，透明度21/255；浅色主题：白色，透明度64/255
        return QColor(255, 255, 255, 21 if isDarkTheme() else 64)

    def _pressedBackgroundColor(self):
        # 按下状态背景色：根据主题返回不同透明度的白色
        # 深色主题：白色，透明度8/255；浅色主题：白色，透明度64/255
        return QColor(255, 255, 255, 8 if isDarkTheme() else 64)

    def getBorderRadius(self):
        # 获取圆角半径：返回当前圆角半径值
        return self._borderRadius

    def setBorderRadius(self, radius: int):
        # 设置圆角半径：更新半径值并刷新界面（重绘）
        self._borderRadius = radius
        self.update()

    def paintEvent(self, e):
        # 创建画家对象：用于在当前部件上绘制内容
        painter = QPainter(self)
        # 设置渲染提示：启用抗锯齿（使图形边缘更平滑）
        painter.setRenderHints(QPainter.Antialiasing)

        # 获取部件宽高：w为宽度，h为高度
        w, h = self.width(), self.height()
        # 圆角半径：r为当前设置的圆角半径
        r = self.borderRadius
        # 直径：d为圆角直径（半径的2倍，用于圆弧计算）
        d = 2 * r

        # 判断当前主题：isDark为True表示深色主题，False表示浅色主题
        isDark = isDarkTheme()

        # 绘制顶部边框路径
        path = QPainterPath()  # 创建路径对象：用于定义边框的形状
        # 移动到右下角圆弧起点：参数依次为x坐标、y坐标、宽度、高度、起始角度（240度）
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        # 绘制右下角圆弧：参数同上，起始角度225度，跨越角度-60度（顺时针绘制60度）
        path.arcTo(1, h - d - 1, d, d, 225, -60)
        # 绘制左侧垂直线：从右下角圆弧终点连接到左上角圆弧起点
        path.lineTo(1, r)
        # 绘制左上角圆弧：起始角度-180度（左侧水平线），跨越角度-90度（顺时针绘制90度）
        path.arcTo(1, 1, d, d, -180, -90)
        # 绘制顶部水平线：从左上角圆弧终点连接到右上角圆弧起点
        path.lineTo(w - r, 1)
        # 绘制右上角圆弧：起始角度90度（顶部垂直线），跨越角度-90度（顺时针绘制90度）
        path.arcTo(w - d - 1, 1, d, d, 90, -90)
        # 绘制右侧垂直线：从右上角圆弧终点连接到右下角圆弧起点
        path.lineTo(w - 1, h - r)
        # 绘制右下角剩余圆弧：起始角度0度（右侧垂直线），跨越角度-60度（顺时针绘制60度）
        path.arcTo(w - d - 1, h - d - 1, d, d, 0, -60)

        # 设置顶部边框颜色：默认深色主题为黑色（透明度20/255），浅色主题为黑色（透明度15/255）
        topBorderColor = QColor(0, 0, 0, 20)
        if isDark:
            # 深色主题下：按下状态边框为白色（透明度18/255），悬停状态为白色（透明度13/255）
            if self.isPressed:
                topBorderColor = QColor(255, 255, 255, 18)
            elif self.isHover:
                topBorderColor = QColor(255, 255, 255, 13)
        else:
            # 浅色主题下：固定为黑色（透明度15/255）
            topBorderColor = QColor(0, 0, 0, 15)

        # 绘制顶部边框：使用当前路径和设置的边框颜色
        painter.strokePath(path, topBorderColor)

        # 绘制底部边框路径
        path = QPainterPath()  # 创建新路径对象（底部边框路径）
        # 移动到右下角圆弧起点（与顶部边框相同）
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        # 绘制右下角底部圆弧：起始角度240度，跨越角度30度（顺时针绘制30度）
        path.arcTo(1, h - d - 1, d, d, 240, 30)
        # 绘制底部水平线：从右下角圆弧终点连接到右上角圆弧起点
        path.lineTo(w - r - 1, h - 1)
        # 绘制右上角底部圆弧：起始角度270度（底部水平线），跨越角度30度（顺时针绘制30度）
        path.arcTo(w - d - 1, h - d - 1, d, d, 270, 30)

        # 设置底部边框颜色：默认与顶部边框颜色相同
        bottomBorderColor = topBorderColor
        # 浅色主题下：悬停且未按下时，底部边框颜色加深（黑色，透明度27/255）
        if not isDark and self.isHover and not self.isPressed:
            bottomBorderColor = QColor(0, 0, 0, 27)

        # 绘制底部边框：使用当前路径和设置的边框颜色
        painter.strokePath(path, bottomBorderColor)

        # 绘制背景
        painter.setPen(Qt.NoPen)  # 取消边框笔（背景填充不需要边框）
        # 调整绘制区域：原矩形向内缩进1像素（避免与边框重叠）
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(self.backgroundColor)  # 设置背景画刷：使用当前背景色（由状态决定）
        painter.drawRoundedRect(rect, r, r)  # 绘制圆角矩形背景：参数为区域、x方向圆角半径、y方向圆角半径

    # 定义圆角半径属性：通过pyqtProperty将get/set方法暴露为Qt属性，支持动画和样式表
    borderRadius = pyqtProperty(int, getBorderRadius, setBorderRadius)

class SimpleCardWidget(CardWidget):
    """ 
    简化版卡片组件：继承自CardWidget，去除复杂边框效果，仅保留基础背景和简单边框，
    所有状态（正常/悬停/按下）使用相同背景色，适用于无需交互反馈的场景。
    """

    def __init__(self, parent=None):
        # 调用父类构造方法初始化
        super().__init__(parent)

    def _normalBackgroundColor(self):
        # 正常状态背景色：与CardWidget相同（深色主题13/255透明度，浅色主题170/255透明度）
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        # 悬停状态背景色：与正常状态相同（无悬停效果）
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        # 按下状态背景色：与正常状态相同（无按下效果）
        return self._normalBackgroundColor()

    def paintEvent(self, e):
        # 创建画家对象
        painter = QPainter(self)
        # 设置抗锯齿渲染
        painter.setRenderHints(QPainter.Antialiasing)
        # 设置背景画刷：使用当前背景色
        painter.setBrush(self.backgroundColor)

        # 设置边框颜色：深色主题为黑色（透明度48/255），浅色主题为黑色（透明度12/255）
        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 48))
        else:
            painter.setPen(QColor(0, 0, 0, 12))

        # 获取圆角半径
        r = self.borderRadius
        # 绘制带边框的圆角矩形：区域向内缩进1像素，圆角半径r
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)

class ElevatedCardWidget(SimpleCardWidget):
    """ 
    带阴影与悬浮效果的卡片组件：继承自SimpleCardWidget，添加阴影动画和悬浮提升效果，
    鼠标悬停时阴影加深且卡片轻微上浮，增强视觉层次感，适用于需要突出显示的交互元素。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建阴影动画实例：目标为当前部件，悬停时阴影颜色为黑色（透明度20/255）
        self.shadowAni = DropShadowAnimation(self, hoverColor=QColor(0, 0, 0, 20))
        self.shadowAni.setOffset(0, 5)  # 设置阴影偏移：x方向0像素，y方向5像素（向下偏移）
        self.shadowAni.setBlurRadius(38)  # 设置阴影模糊半径：38像素（控制阴影扩散范围）

        # 创建位置动画实例：用于实现卡片悬浮时的位置变化，目标属性为pos（位置）
        self.elevatedAni = QPropertyAnimation(self, b'pos', self)
        self.elevatedAni.setDuration(100)  # 设置动画持续时间：100毫秒（平滑过渡）

        self._originalPos = self.pos()  # 记录初始位置：用于鼠标离开时恢复原位
        self.setBorderRadius(8)  # 设置圆角半径：8像素（比基础卡片更大，视觉更柔和）

    def enterEvent(self, e):
        # 鼠标进入事件：调用父类方法后启动悬浮动画
        super().enterEvent(e)

        # 若动画未运行，更新初始位置（避免多次进入导致位置偏移）
        if self.elevatedAni.state() != QPropertyAnimation.Running:
            self._originalPos = self.pos()

        # 启动悬浮提升动画：从当前位置移动到向上3像素的位置（视觉上浮效果）
        self._startElevateAni(self.pos(), self.pos() - QPoint(0, 3))

    def leaveEvent(self, e):
        # 鼠标离开事件：调用父类方法后恢复初始位置
        super().leaveEvent(e)
        self._startElevateAni(self.pos(), self._originalPos)

    def mousePressEvent(self, e):
        # 鼠标按下事件：调用父类方法后取消悬浮效果（按下时恢复原位）
        super().mousePressEvent(e)
        self._startElevateAni(self.pos(), self._originalPos)

    def _startElevateAni(self, start, end):
        # 设置动画起始值和结束值，启动动画
        self.elevatedAni.setStartValue(start)  # 起始位置
        self.elevatedAni.setEndValue(end)      # 结束位置
        self.elevatedAni.start()               # 启动动画

    def _hoverBackgroundColor(self):
        # 悬停状态背景色：深色主题白色（16/255透明度），浅色主题纯白（255/255透明度）
        return QColor(255, 255, 255, 16) if isDarkTheme() else QColor(255, 255, 255)

    def _pressedBackgroundColor(self):
        # 按下状态背景色：深色主题白色（6/255透明度），浅色主题白色（118/255透明度）
        return QColor(255, 255, 255, 6 if isDarkTheme() else 118)

class CardSeparator(QWidget):
    """ 
    卡片分隔线组件：用于在卡片内部分隔不同内容区域，提供主题自适应的线条样式。
    特点：固定高度为3像素，线条颜色随主题变化（深色主题白色半透明，浅色主题黑色半透明）
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)  # 调用父类QWidget构造方法
        self.setFixedHeight(3)  # 设置固定高度：3像素

    def paintEvent(self, e):
        painter = QPainter(self)  # 创建画家对象
        painter.setRenderHints(QPainter.Antialiasing)  # 启用抗锯齿

        # 设置线条颜色：深色主题白色（透明度46/255），浅色主题黑色（透明度12/255）
        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 46))
        else:
            painter.setPen(QColor(0, 0, 0, 12))
        
        # 绘制水平线：从(2,1)到(width-2,1)，线宽1像素，居中显示
        painter.drawLine(2, 1, self.width() - 2, 1)


class HeaderCardWidget(SimpleCardWidget):
    """ 
    带标题的卡片组件：继承自SimpleCardWidget，添加标题区域和分隔线，
    适用于需要显示标题和内容的场景，支持自定义标题文本。
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headerView = QWidget(self)
        self.headerLabel = QLabel(self)
        self.separator = CardSeparator(self)
        self.view = QWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.headerLayout = QHBoxLayout(self.headerView)
        self.viewLayout = QHBoxLayout(self.view)

        self.headerLayout.addWidget(self.headerLabel)
        self.headerLayout.setContentsMargins(24, 0, 16, 0)
        self.headerView.setFixedHeight(48)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.headerView)
        self.vBoxLayout.addWidget(self.separator)
        self.vBoxLayout.addWidget(self.view)

        self.viewLayout.setContentsMargins(24, 24, 24, 24)
        setFont(self.headerLabel, 15, QFont.DemiBold)

        self.view.setObjectName('view')
        self.headerView.setObjectName('headerView')
        self.headerLabel.setObjectName('headerLabel')
        FluentStyleSheet.CARD_WIDGET.apply(self)

        self._postInit()

    @__init__.register
    def _(self, title: str, parent=None):
        self.__init__(parent)
        self.setTitle(title)

    def getTitle(self):
        return self.headerLabel.text()

    def setTitle(self, title: str):
        self.headerLabel.setText(title)

    def _postInit(self):
        pass

    title = pyqtProperty(str, getTitle, setTitle)


class CardGroupWidget(QWidget):
    """ 
    卡片组组件：用于组织多个卡片组件，提供统一的布局和样式，
    适用于需要展示多个相关信息的场景，支持自定义标题和内容。
    """
    def __init__(self, icon: Union[str, FluentIconBase, QIcon], title: str, content: str, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()

        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title)
        self.contentLabel = CaptionLabel(content)
        self.textLayout = QVBoxLayout()

        self.separator = CardSeparator()

        self.__initWidget()

    def __initWidget(self):
        self.separator.hide()
        self.iconWidget.setFixedSize(20, 20)
        self.contentLabel.setTextColor(QColor(96, 96, 96), QColor(206, 206, 206))

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addWidget(self.separator)

        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.contentLabel)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.textLayout)
        self.hBoxLayout.addStretch(1)

        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.setContentsMargins(24, 10, 24, 10)
        self.textLayout.setContentsMargins(0, 0, 0, 0)
        self.textLayout.setSpacing(0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, text: str):
        self.titleLabel.setText(text)

    def content(self):
        return self.contentLabel.text()

    def setContent(self, text: str):
        self.contentLabel.setText(text)

    def icon(self):
        return self.iconWidget.icon

    def setIcon(self, icon: Union[str, FluentIconBase, QIcon]):
        self.iconWidget.setIcon(icon)

    def setIconSize(self, size: QSize):
        self.iconWidget.setFixedSize(size)

    def setSeparatorVisible(self, isVisible: bool):
        self.separator.setVisible(isVisible)

    def isSeparatorVisible(self):
        return self.separator.isVisible()

    def addWidget(self, widget: QWidget, stretch=0):
        self.hBoxLayout.addWidget(widget, stretch=stretch)


class GroupHeaderCardWidget(HeaderCardWidget):
    """ 
    分组标题卡片组件：继承自HeaderCardWidget，添加分组布局和分隔线，
    适用于需要展示多个相关信息的场景，支持自定义标题和内容。
    """

    def _postInit(self):
        super()._postInit()
        self.groupWidgets = []  # type: List[CardGroupWidget]
        self.groupLayout = QVBoxLayout()

        self.groupLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.groupLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.addLayout(self.groupLayout)

    def addGroup(self, icon: Union[str, FluentIconBase, QIcon], title: str, content: str, widget: QWidget, stretch=0) -> CardGroupWidget:
        """ 
        添加分组：创建一个新的卡片组组件，包含图标、标题、内容和子组件，
        并将其添加到分组布局中。如果不是第一个分组，会设置前一个分组的分隔线可见。
        """
        group = CardGroupWidget(icon, title, content, self)
        group.addWidget(widget, stretch=stretch)

        if self.groupWidgets:
            self.groupWidgets[-1].setSeparatorVisible(True)

        self.groupLayout.addWidget(group)
        self.groupWidgets.append(group)
        return group

    def groupCount(self):
        return len(self.groupWidgets)