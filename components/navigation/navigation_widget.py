# coding:utf-8
# 导入必要的类型提示
from typing import Union, List

# 导入PyQt5相关模块
from PyQt5.QtCore import (Qt, pyqtSignal, QRect, QRectF, QPropertyAnimation, pyqtProperty, QMargins,
                          QEasingCurve, QPoint, QEvent)
from PyQt5.QtGui import QColor, QPainter, QPen, QIcon, QCursor, QFont, QBrush, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QVBoxLayout
# 导入双端队列，用于树节点遍历
from collections import deque

# 导入自定义的配置和样式相关模块
from common.config import isDarkTheme
from common.style_sheet import themeColor
from common.icon import drawIcon, toQIcon
from common.icon import FluentIcon as FIF
from common.color import autoFallbackThemeColor
from common.font import setFont
from components.widgets.scroll_area import ScrollArea
from components.widgets.label import AvatarWidget
from components.widgets.info_badge import InfoBadgeManager, InfoBadgePosition


class NavigationWidget(QWidget):
    """ 导航组件基类
    
    这是所有导航组件的基类，提供了基本的导航项功能和交互行为。
    """

    
    clicked = pyqtSignal(bool)  # 定义点击信号，参数表示是否由用户触发
    
    selectedChanged = pyqtSignal(bool)  # 定义选中状态改变信号
    # 定义展开状态的宽度常量
    EXPAND_WIDTH = 312

    def __init__(self, isSelectable: bool, parent=None):
        # 调用父类的初始化方法
        super().__init__(parent)
        # 设置初始状态：紧凑模式、未选中、未按下、鼠标未进入、是否可选中
        self.isCompacted = True  # 是否处于紧凑模式
        self.isSelected = False  # 是否被选中
        self.isPressed = False   # 是否被按下
        self.isEnter = False     # 鼠标是否进入
        self.isSelectable = isSelectable  # 是否可以被选中
        self.treeParent = None   # 树形结构中的父节点
        self.nodeDepth = 0       # 节点在树中的深度

        # 设置文本颜色
        self.lightTextColor = QColor(0, 0, 0)   # 亮色主题下的文本颜色
        self.darkTextColor = QColor(255, 255, 255)  # 暗色主题下的文本颜色

        # 设置初始固定大小
        self.setFixedSize(40, 36)

    def enterEvent(self, e):
        """ 鼠标进入事件处理 """
        self.isEnter = True  # 设置鼠标进入状态
        self.update()        # 更新界面显示

    def leaveEvent(self, e):
        """ 鼠标离开事件处理 """
        self.isEnter = False   # 重置鼠标进入状态
        self.isPressed = False  # 重置按下状态
        self.update()          # 更新界面显示

    def mousePressEvent(self, e):
        """ 鼠标按下事件处理 """
        super().mousePressEvent(e)  # 调用父类方法
        self.isPressed = True       # 设置按下状态
        self.update()               # 更新界面显示

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件处理 """
        super().mouseReleaseEvent(e)  # 调用父类方法
        self.isPressed = False        # 重置按下状态
        self.update()                 # 更新界面显示
        self.clicked.emit(True)       # 发出点击信号，参数为True表示由用户触发

    def click(self):
        """ 模拟点击操作 """
        self.clicked.emit(True)  # 发出点击信号

    def setCompacted(self, isCompacted: bool):
        """ 设置组件是否处于紧凑模式
        
        Parameters
        ----------
        isCompacted: bool
            是否设置为紧凑模式
        """
        if isCompacted == self.isCompacted:
            return  # 如果状态没有改变，直接返回

        self.isCompacted = isCompacted  # 更新紧凑模式状态
        if isCompacted:
            self.setFixedSize(40, 36)   # 紧凑模式下的大小
        else:
            self.setFixedSize(self.EXPAND_WIDTH, 36)  # 展开模式下的大小

        self.update()  # 更新界面显示

    def setSelected(self, isSelected: bool):
        """ 设置按钮是否被选中
        
        Parameters
        ----------
        isSelected: bool
            按钮是否被选中
        """
        if not self.isSelectable:
            return  # 如果不可选中，直接返回

        self.isSelected = isSelected  # 更新选中状态
        self.update()                 # 更新界面显示
        self.selectedChanged.emit(isSelected)  # 发出选中状态改变信号

    def textColor(self):
        """ 根据当前主题返回适当的文本颜色 """
        return self.darkTextColor if isDarkTheme() else self.lightTextColor

    def setLightTextColor(self, color):
        """ 设置亮色主题模式下的文本颜色
        
        Parameters
        ----------
        color: QColor or str
            要设置的颜色
        """
        self.lightTextColor = QColor(color)  # 更新亮色主题文本颜色
        self.update()                        # 更新界面显示

    def setDarkTextColor(self, color):
        """ 设置暗色主题模式下的文本颜色
        
        Parameters
        ----------
        color: QColor or str
            要设置的颜色
        """
        self.darkTextColor = QColor(color)  # 更新暗色主题文本颜色
        self.update()                       # 更新界面显示

    def setTextColor(self, light, dark):
        """ 同时设置亮色/暗色主题模式下的文本颜色
        
        Parameters
        ----------
        light: QColor or str
            亮色主题下的文本颜色
        dark: QColor or str
            暗色主题下的文本颜色
        """
        self.setLightTextColor(light)  # 设置亮色主题文本颜色
        self.setDarkTextColor(dark)    # 设置暗色主题文本颜色


class NavigationPushButton(NavigationWidget):
    """ 导航推送按钮
    
    一种可显示图标和文本的导航按钮，是最常用的导航组件。
    """

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            要显示的图标
        
        text: str
            按钮的文本
        
        isSelectable: bool
            按钮是否可以被选中
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(isSelectable=isSelectable, parent=parent)  # 调用父类初始化方法

        self._icon = icon  # 存储图标
        self._text = text  # 存储文本
        self.lightIndicatorColor = QColor()  # 亮色主题下的指示器颜色
        self.darkIndicatorColor = QColor()   # 暗色主题下的指示器颜色

        setFont(self)  # 设置字体

    def text(self):
        """ 获取按钮文本 """
        return self._text

    def setText(self, text: str):
        """ 设置按钮文本
        
        Parameters
        ----------
        text: str
            新的按钮文本
        """
        self._text = text  # 更新文本
        self.update()      # 更新界面显示

    def icon(self):
        """ 获取按钮图标，转换为QIcon类型 """
        return toQIcon(self._icon)

    def setIcon(self, icon: Union[str, QIcon, FIF]):
        """ 设置按钮图标
        
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            新的按钮图标
        """
        self._icon = icon  # 更新图标
        self.update()      # 更新界面显示

    def _margins(self):
        """ 获取按钮的边距，内部方法 """
        return QMargins(0, 0, 0, 0)

    def _canDrawIndicator(self):
        """ 判断是否可以绘制指示器，内部方法 """
        return self.isSelected

    def setIndicatorColor(self, light, dark):
        """ 设置指示器在亮色/暗色主题下的颜色
        
        Parameters
        ----------
        light: QColor or str
            亮色主题下的指示器颜色
        dark: QColor or str
            暗色主题下的指示器颜色
        """
        self.lightIndicatorColor = QColor(light)  # 更新亮色主题指示器颜色
        self.darkIndicatorColor = QColor(dark)    # 更新暗色主题指示器颜色
        self.update()                             # 更新界面显示

    def paintEvent(self, e):
        """ 绘制按钮界面 """
        painter = QPainter(self)  # 创建画家对象
        # 设置渲染提示，提高绘制质量
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)  # 设置无 pen

        if self.isPressed:
            painter.setOpacity(0.7)  # 按下状态下降低透明度
        if not self.isEnabled():
            painter.setOpacity(0.4)  # 禁用状态下降低透明度

        # 绘制背景
        c = 255 if isDarkTheme() else 0  # 根据主题获取颜色值
        m = self._margins()              # 获取边距
        pl, pr = m.left(), m.right()     # 左右边距
        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())  # 转换为全局坐标

        if self._canDrawIndicator():
            # 绘制选中状态的背景
            painter.setBrush(QColor(c, c, c, 6 if self.isEnter else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

            # 绘制指示器
            painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor)) 
            painter.drawRoundedRect(pl, 10, 3, 16, 1.5, 1.5) # 绘制指示器，位置为pl，圆角半径为10，边框宽度为3，宽度为16，高度为1.5
        elif self.isEnter and self.isEnabled() and globalRect.contains(QCursor.pos()):
            # 绘制鼠标悬停状态的背景
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # 绘制图标
        drawIcon(self._icon, painter, QRectF(11.5+pl, 10, 16, 16))

        # 绘制文本
        if self.isCompacted:
            return  # 紧凑模式下不显示文本

        painter.setFont(self.font())      # 设置字体
        painter.setPen(self.textColor())  # 设置文本颜色

        # 计算文本起始位置
        left = 44 + pl if not self.icon().isNull() else pl + 16
        # 绘制文本
        painter.drawText(QRectF(left, 0, self.width()-13-left-pr, self.height()), Qt.AlignVCenter, self.text())


class NavigationToolButton(NavigationPushButton):
    """ 导航工具按钮
    
    一种简化的导航按钮，通常只显示图标，不可选中。
    """

    def __init__(self, icon: Union[str, QIcon, FIF], parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            要显示的图标
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(icon, '', False, parent)  # 调用父类初始化方法，文本为空，不可选中

    def setCompacted(self, isCompacted: bool):
        """ 设置组件是否处于紧凑模式
        
        重写父类方法，工具按钮始终保持相同大小
        
        Parameters
        ----------
        isCompacted: bool
            是否设置为紧凑模式（此参数在这里无效）
        """
        self.setFixedSize(40, 36)  # 始终保持固定大小


class NavigationSeparator(NavigationWidget):
    """ 导航分隔符
    
    用于在导航栏中分隔不同组的项目。
    """

    def __init__(self, parent=None):
        super().__init__(False, parent=parent)  # 调用父类初始化方法，不可选中
        self.setCompacted(True)  # 默认设置为紧凑模式

    def setCompacted(self, isCompacted: bool):
        """ 设置分隔符是否处于紧凑模式
        
        Parameters
        ----------
        isCompacted: bool
            是否设置为紧凑模式
        """
        if isCompacted:
            self.setFixedSize(48, 3)  # 紧凑模式下的大小
        else:
            self.setFixedSize(self.EXPAND_WIDTH + 10, 3)  # 展开模式下的大小

        self.update()  # 更新界面显示

    def paintEvent(self, e):
        """ 绘制分隔符 """
        painter = QPainter(self)  # 创建画家对象
        c = 255 if isDarkTheme() else 0  # 根据主题获取颜色值
        pen = QPen(QColor(c, c, c, 15))  # 创建画笔
        pen.setCosmetic(True)  # 设置为 cosmetics pen，确保线条宽度不受变换影响
        painter.setPen(pen)    # 设置画笔
        painter.drawLine(0, 1, self.width(), 1)  # 绘制分隔线



class NavigationTreeItem(NavigationPushButton):
    """ 导航树项目组件
    
    用于导航树中的项目，支持展开/折叠功能。
    """

    # 定义项目点击信号，参数为是否由用户触发和是否点击了箭头
    itemClicked = pyqtSignal(bool, bool)    # triggerByUser, clickArrow

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            要显示的图标
        
        text: str
            项目的文本
        
        isSelectable: bool
            项目是否可以被选中
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(icon, text, isSelectable, parent)  # 调用父类初始化方法
        self._arrowAngle = 0  # 箭头的初始角度
        # 创建箭头旋转动画
        self.rotateAni = QPropertyAnimation(self, b'arrowAngle', self)

    def setExpanded(self, isExpanded: bool):
        """ 设置项目的展开状态
        
        Parameters
        ----------
        isExpanded: bool
            是否展开项目
        """
        self.rotateAni.stop()  # 停止当前动画
        # 设置动画结束值：展开为180度，折叠为0度
        self.rotateAni.setEndValue(180 if isExpanded else 0)
        self.rotateAni.setDuration(150)  # 设置动画持续时间
        self.rotateAni.start()  # 开始动画

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件处理
        
        重写父类方法，添加对箭头点击的检测
        """
        super().mouseReleaseEvent(e)  # 调用父类方法
        # 检测是否点击了箭头区域
        clickArrow = QRectF(self.width()-30, 8, 20, 20).contains(e.pos())
        # 发出项目点击信号，传递是否由用户触发和是否点击了箭头
        self.itemClicked.emit(True, clickArrow and not self.parent().isLeaf())
        self.update()  # 更新界面显示

    def _canDrawIndicator(self):
        """ 判断是否可以绘制指示器，内部方法
        
        重写父类方法，考虑树结构中的节点状态
        """
        p = self.parent()   # 获取父部件（NavigationTreeWidget类型）
        if p.isLeaf() or p.isSelected:
            return p.isSelected  # 如果是叶节点或父节点被选中，则根据父节点选中状态决定

        # 检查子节点是否有需要显示指示器的情况
        for child in p.treeChildren:
            if child.itemWidget._canDrawIndicator() and not child.isVisible():
                return True

        return False

    def _margins(self):
        """ 获取边距，内部方法
        
        重写父类方法，根据树节点深度和子节点情况调整边距
        """
        p = self.parent()  # 获取父部件
        # 左侧边距根据节点深度调整，右侧边距根据是否有子节点调整
        return QMargins(p.nodeDepth*28, 0, 20*bool(p.treeChildren), 0)

    def paintEvent(self, e):
        """ 绘制项目界面
        
        重写父类方法，添加箭头的绘制
        """
        super().paintEvent(e)  # 调用父类方法
        # 紧凑模式或没有子节点时不绘制箭头
        if self.isCompacted or not self.parent().treeChildren:
            return

        painter = QPainter(self)  # 创建画家对象
        painter.setRenderHints(QPainter.Antialiasing)  # 设置渲染提示
        painter.setPen(Qt.NoPen)  # 设置无 pen

        if self.isPressed:
            painter.setOpacity(0.7)  # 按下状态下降低透明度
        if not self.isEnabled():
            painter.setOpacity(0.4)  # 禁用状态下降低透明度

        # 绘制箭头
        painter.translate(self.width() - 20, 18)  # 移动到箭头位置
        painter.rotate(self.arrowAngle)          # 旋转到指定角度
        FIF.ARROW_DOWN.render(painter, QRectF(-5, -5, 9.6, 9.6))  # 渲染箭头图标

    def getArrowAngle(self):
        """ 获取箭头角度（用于属性动画） """
        return self._arrowAngle

    def setArrowAngle(self, angle):
        """ 设置箭头角度（用于属性动画）
        
        Parameters
        ----------
        angle: float
            箭头的旋转角度
        """
        self._arrowAngle = angle  # 更新箭头角度
        self.update()             # 更新界面显示

    # 将箭头角度定义为Qt属性，使其可以用于属性动画
    arrowAngle = pyqtProperty(float, getArrowAngle, setArrowAngle)


class NavigationTreeWidgetBase(NavigationWidget):
    """ 导航树部件基类
    
    定义导航树部件的基本接口。
    """

    def addChild(self, child):
        """ 添加子节点
        
        Parameters
        ----------
        child: NavigationTreeWidgetBase
            要添加的子节点
        
        Raises
        ------
        NotImplementedError
            此方法需要在子类中实现
        """
        raise NotImplementedError

    def insertChild(self, index: int, child: NavigationWidget):
        """ 插入子节点
        
        Parameters
        ----------
        index: int
            插入位置的索引
        
        child: NavigationTreeWidgetBase
            要插入的子节点
        
        Raises
        ------
        NotImplementedError
            此方法需要在子类中实现
        """
        raise NotImplementedError

    def removeChild(self, child: NavigationWidget):
        """ 移除子节点
        
        Parameters
        ----------
        child: NavigationTreeWidgetBase
            要移除的子节点
        
        Raises
        ------
        NotImplementedError
            此方法需要在子类中实现
        """
        raise NotImplementedError

    def isRoot(self):
        """ 判断是否为根节点
        
        Returns
        -------
        bool
            是否为根节点
        """
        return True

    def isLeaf(self):
        """ 判断是否为叶节点
        
        Returns
        -------
        bool
            是否为叶节点
        """
        return True

    def setExpanded(self, isExpanded: bool):
        """ 设置节点的展开状态
        
        Parameters
        ----------
        isExpanded: bool
            是否展开节点
        
        Raises
        ------
        NotImplementedError
            此方法需要在子类中实现
        """
        raise NotImplementedError

    def childItems(self) -> list:
        """ 返回子节点列表
        
        Returns
        -------
        list
            子节点列表
        
        Raises
        ------
        NotImplementedError
            此方法需要在子类中实现
        """
        raise NotImplementedError


class NavigationTreeWidget(NavigationTreeWidgetBase):
    """ 导航树部件
    
    实现导航树功能，支持节点的展开、折叠和层次结构。
    """

    expanded = pyqtSignal()

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            节点的图标
        
        text: str
            节点的文本
        
        isSelectable: bool
            节点是否可以被选中
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(isSelectable, parent)  # 调用父类初始化方法

        self.treeChildren = []  # 存储子节点的列表
        self.isExpanded = False  # 是否展开
        self._icon = icon  # 存储图标

        # 创建树项目部件
        self.itemWidget = NavigationTreeItem(icon, text, isSelectable, self)
        # 创建垂直布局
        self.vBoxLayout = QVBoxLayout(self)
        # 创建展开动画
        self.expandAni = QPropertyAnimation(self, b'geometry', self)

        self.__initWidget()  # 初始化部件

    def __initWidget(self):
        """ 初始化部件，内部方法 """
        self.vBoxLayout.setSpacing(4)  # 设置布局间距
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)  # 设置布局边距
        # 添加项目部件到布局
        self.vBoxLayout.addWidget(self.itemWidget, 0, Qt.AlignTop)

        # 连接信号与槽
        self.itemWidget.itemClicked.connect(self._onClicked)
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 连接展开动画的信号
        self.expandAni.valueChanged.connect(lambda g: self.setFixedSize(g.size()))
        self.expandAni.valueChanged.connect(self.expanded)
        # 动画完成后使父部件的布局无效，触发重新布局
        self.expandAni.finished.connect(self.parentWidget().layout().invalidate)

    def addChild(self, child):
        """ 添加子节点
        
        Parameters
        ----------
        child: NavigationTreeWidget
            要添加的子节点
        """
        self.insertChild(-1, child)  # 调用insertChild方法，索引为-1表示添加到末尾

    def text(self):
        """ 获取节点文本 """
        return self.itemWidget.text()

    def icon(self):
        """ 获取节点图标 """
        return self.itemWidget.icon()

    def setText(self, text):
        """ 设置节点文本
        
        Parameters
        ----------
        text: str
            新的节点文本
        """
        self.itemWidget.setText(text)  # 设置项目部件的文本

    def setIcon(self, icon: Union[str, QIcon, FIF]):
        """ 设置节点图标
        
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            新的节点图标
        """
        self.itemWidget.setIcon(icon)  # 设置项目部件的图标

    def textColor(self):
        """ 获取节点的文本颜色 """
        return self.itemWidget.textColor()

    def setLightTextColor(self, color):
        """ 设置亮色主题模式下的文本颜色
        
        Parameters
        ----------
        color: QColor or str
            要设置的颜色
        """
        self.itemWidget.setLightTextColor(color)  # 设置项目部件的亮色主题文本颜色

    def setDarkTextColor(self, color):
        """ 设置暗色主题模式下的文本颜色
        
        Parameters
        ----------
        color: QColor or str
            要设置的颜色
        """
        self.itemWidget.setDarkTextColor(color)  # 设置项目部件的暗色主题文本颜色

    def setTextColor(self, light, dark):
        """ 同时设置亮色/暗色主题模式下的文本颜色
        
        Parameters
        ----------
        light: QColor or str
            亮色主题下的文本颜色
        dark: QColor or str
            暗色主题下的文本颜色
        """
        self.lightTextColor = QColor(light)  # 更新亮色主题文本颜色
        self.darkTextColor = QColor(dark)    # 更新暗色主题文本颜色
        self.itemWidget.setTextColor(light, dark)  # 设置项目部件的文本颜色

    def setIndicatorColor(self, light, dark):
        """ 设置指示器在亮色/暗色主题下的颜色
        
        Parameters
        ----------
        light: QColor or str
            亮色主题下的指示器颜色
        dark: QColor or str
            暗色主题下的指示器颜色
        """
        self.itemWidget.setIndicatorColor(light, dark)  # 设置项目部件的指示器颜色

    def setFont(self, font: QFont):
        """ 设置字体
        
        Parameters
        ----------
        font: QFont
            要设置的字体
        """
        super().setFont(font)  # 调用父类方法
        self.itemWidget.setFont(font)  # 设置项目部件的字体

    def clone(self):
        """ 克隆当前节点及其所有子节点
        
        Returns
        -------
        NavigationTreeWidget
            克隆后的节点
        """
        # 创建新节点
        root = NavigationTreeWidget(self._icon, self.text(), self.isSelectable, self.parent())
        # 复制属性
        root.setSelected(self.isSelected)
        root.setFixedSize(self.size())
        root.setTextColor(self.lightTextColor, self.darkTextColor)
        root.setIndicatorColor(self.itemWidget.lightIndicatorColor, self.itemWidget.darkIndicatorColor)
        root.nodeDepth = self.nodeDepth

        # 连接信号
        root.clicked.connect(self.clicked)
        self.selectedChanged.connect(root.setSelected)

        # 递归克隆子节点
        for child in self.treeChildren:
            root.addChild(child.clone())

        return root

    def suitableWidth(self):
        """ 计算节点的合适宽度
        
        Returns
        -------
        int
            合适的宽度值
        """
        m = self.itemWidget._margins()  # 获取边距
        # 计算左侧偏移量
        left = 57 + m.left() if not self.icon().isNull() else m.left() + 29
        # 计算文本宽度
        tw = self.itemWidget.fontMetrics().boundingRect(self.text()).width()
        # 返回总宽度
        return left + tw + m.right()

    def insertChild(self, index, child):
        """ 在指定位置插入子节点
        
        Parameters
        ----------
        index: int
            插入位置的索引
        
        child: NavigationTreeWidget
            要插入的子节点
        """
        if child in self.treeChildren:
            return  # 如果子节点已存在，直接返回

        # 设置子节点的父节点和深度
        child.treeParent = self
        child.nodeDepth = self.nodeDepth + 1
        child.setVisible(self.isExpanded)  # 根据当前节点的展开状态设置子节点的可见性
        # 连接子节点的展开动画信号
        child.expandAni.valueChanged.connect(lambda: self.setFixedSize(self.sizeHint()))
        child.expandAni.valueChanged.connect(self.expanded)

        # 递归连接高度变化信号到父节点
        p = self.treeParent
        while p:
            child.expandAni.valueChanged.connect(lambda v, p=p: p.setFixedSize(p.sizeHint()))
            p = p.treeParent

        if index < 0:
            index = len(self.treeChildren)  # 索引为负表示添加到末尾

        index += 1  # 项目部件应始终位于第一个位置
        self.treeChildren.insert(index, child)  # 添加到子节点列表
        self.vBoxLayout.insertWidget(index, child, 0, Qt.AlignTop)  # 添加到布局

        # 调整高度
        if self.isExpanded:
            # 增加当前节点的高度
            self.setFixedHeight(self.height() + child.height() + self.vBoxLayout.spacing())

            # 递归调整父节点的大小
            p = self.treeParent
            while p:
                p.setFixedSize(p.sizeHint())
                p = p.treeParent

        self.update()  # 更新界面显示

    def removeChild(self, child):
        """ 移除子节点
        
        Parameters
        ----------
        child: NavigationTreeWidget
            要移除的子节点
        """
        self.treeChildren.remove(child)  # 从子节点列表中移除
        self.vBoxLayout.removeWidget(child)  # 从布局中移除

    def childItems(self) -> list:
        """ 返回子节点列表
        
        Returns
        -------
        list
            子节点列表
        """
        return self.treeChildren

    def setExpanded(self, isExpanded: bool, ani=False):
        """ 设置节点的展开状态
        
        Parameters
        ----------
        isExpanded: bool
            是否展开节点
        
        ani: bool, optional
            是否使用动画效果，默认为False
        """
        if isExpanded == self.isExpanded:
            return  # 如果状态没有改变，直接返回

        self.isExpanded = isExpanded  # 更新展开状态
        self.itemWidget.setExpanded(isExpanded)  # 设置项目部件的展开状态

        # 设置所有子节点的可见性和大小
        for child in self.treeChildren:
            child.setVisible(isExpanded)
            child.setFixedSize(child.sizeHint())

        if ani:
            # 使用动画效果
            self.expandAni.stop()  # 停止当前动画
            self.expandAni.setStartValue(self.geometry())  # 设置动画起始值
            self.expandAni.setEndValue(QRect(self.pos(), self.sizeHint()))  # 设置动画结束值
            self.expandAni.setDuration(120)  # 设置动画持续时间
            self.expandAni.setEasingCurve(QEasingCurve.OutQuad)  # 设置动画缓动曲线
            self.expandAni.start()  # 开始动画
        else:
            self.setFixedSize(self.sizeHint())  # 直接设置大小

    def isRoot(self):
        """ 判断是否为根节点
        
        Returns
        -------
        bool
            是否为根节点
        """
        return self.treeParent is None

    def isLeaf(self):
        """ 判断是否为叶节点
        
        Returns
        -------
        bool
            是否为叶节点
        """
        return len(self.treeChildren) == 0

    def setSelected(self, isSelected: bool):
        """ 设置节点是否被选中
        
        Parameters
        ----------
        isSelected: bool
            节点是否被选中
        """
        super().setSelected(isSelected)  # 调用父类方法
        self.itemWidget.setSelected(isSelected)  # 设置项目部件的选中状态

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件处理
        
        重写父类方法，禁用节点本身的点击响应，点击响应由itemWidget处理
        """
        pass

    def setCompacted(self, isCompacted: bool):
        """ 设置节点是否处于紧凑模式
        
        Parameters
        ----------
        isCompacted: bool
            是否设置为紧凑模式
        """
        super().setCompacted(isCompacted)  # 调用父类方法
        self.itemWidget.setCompacted(isCompacted)  # 设置项目部件的紧凑模式

    def _onClicked(self, triggerByUser, clickArrow):
        """ 处理项目点击事件，内部方法
        
        Parameters
        ----------
        triggerByUser: bool
            是否由用户触发
        
        clickArrow: bool
            是否点击了箭头
        """
        if not self.isCompacted:
            if self.isSelectable and not self.isSelected and not clickArrow:
                # 如果可选中且未被选中且没有点击箭头，则展开节点
                self.setExpanded(True, ani=True)
            else:
                # 否则切换展开状态
                self.setExpanded(not self.isExpanded, ani=True)

        if not clickArrow or self.isCompacted:
            # 如果没有点击箭头或者处于紧凑模式，发出点击信号
            self.clicked.emit(triggerByUser)







class NavigationAvatarWidget(NavigationWidget):
    """ 头像导航部件
    
    显示用户头像和名称的导航部件。
    """

    def __init__(self, name: str, avatar: Union[str, QPixmap, QImage] = None, parent=None):
        """
        Parameters
        ----------
        name: str
            用户名称
        
        avatar: str | QPixmap | QImage, optional
            用户头像，可以是图片路径、QPixmap或QImage对象
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(isSelectable=False, parent=parent)  # 调用父类初始化方法，不可选中
        self.name = name  # 存储用户名称
        self.avatar = AvatarWidget(self)  # 创建头像部件

        self.avatar.setRadius(12)  # 设置头像圆角半径
        self.avatar.setText(name)  # 设置头像显示的文本
        self.avatar.move(8, 6)     # 设置头像位置
        setFont(self)              # 设置字体

        if avatar:
            self.setAvatar(avatar)  # 如果提供了头像，设置头像

    def setName(self, name: str):
        """ 设置用户名称
        
        Parameters
        ----------
        name: str
            新的用户名称
        """
        self.name = name  # 更新用户名称
        self.avatar.setText(name)  # 更新头像显示的文本
        self.update()  # 更新界面显示

    def setAvatar(self, avatar: Union[str, QPixmap, QImage]):
        """ 设置用户头像
        
        Parameters
        ----------
        avatar: str | QPixmap | QImage
            新的用户头像
        """
        self.avatar.setImage(avatar)  # 设置头像图片
        self.avatar.setRadius(12)     # 设置头像圆角半径
        self.update()                 # 更新界面显示

    def paintEvent(self, e):
        """ 绘制头像导航部件 """
        painter = QPainter(self)  # 创建画家对象
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)  # 设置渲染提示

        painter.setPen(Qt.NoPen)  # 设置无 pen

        if self.isPressed:
            painter.setOpacity(0.7)  # 按下状态下降低透明度

        # 绘制背景
        if self.isEnter:
            c = 255 if isDarkTheme() else 0  # 根据主题获取颜色值
            painter.setBrush(QColor(c, c, c, 10))  # 设置背景画刷
            painter.drawRoundedRect(self.rect(), 5, 5)  # 绘制圆角矩形背景

        # 绘制用户名称
        if not self.isCompacted:
            painter.setPen(self.textColor())  # 设置文本颜色
            painter.setFont(self.font())      # 设置字体
            # 绘制文本
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, self.name)


@InfoBadgeManager.register(InfoBadgePosition.NAVIGATION_ITEM)
class NavigationItemInfoBadgeManager(InfoBadgeManager):
    """ 导航项信息徽章管理器
    
    管理导航项上的信息徽章（如未读消息数等）。
    """

    def eventFilter(self, obj, e: QEvent):
        """ 事件过滤器
        
        Parameters
        ----------
        obj: QObject
            要过滤的对象
        
        e: QEvent
            事件对象
        
        Returns
        -------
        bool
            事件是否被处理
        """
        if obj is self.target:
            if e.type() == QEvent.Show:
                self.badge.show()  # 当目标显示时，显示徽章

        return super().eventFilter(obj, e)  # 调用父类方法

    def position(self):
        """ 计算徽章的位置
        
        Returns
        -------
        QPoint
            徽章的位置
        """
        target = self.target
        self.badge.setVisible(target.isVisible())  # 根据目标可见性设置徽章可见性

        if target.isCompacted:
            # 紧凑模式下的位置
            return target.geometry().topRight() - QPoint(self.badge.width() + 2, -2)

        if isinstance(target, NavigationTreeWidget):
            # 树部件的位置调整
            dx = 10 if target.isLeaf() else 35
            x = target.geometry().right() - self.badge.width() - dx
            y = target.y() + 18 - self.badge.height() // 2
        else:
            # 其他部件的位置
            x = target.geometry().right() - self.badge.width() - 10
            y = target.geometry().center().y() - self.badge.height() // 2

        return QPoint(x, y)


class NavigationFlyoutMenu(ScrollArea):
    """ 导航弹出菜单
    
    从导航项弹出的菜单，显示树状结构的导航选项。
    """

    # 定义展开信号
    expanded = pyqtSignal()

    def __init__(self, tree: NavigationTreeWidget, parent=None):
        """
        Parameters
        ----------
        tree: NavigationTreeWidget
            要显示的树部件
        
        parent: QWidget, optional
            父部件
        """
        super().__init__(parent)  # 调用父类初始化方法
        self.view = QWidget(self)  # 创建视图部件

        self.treeWidget = tree      # 存储树部件
        self.treeChildren = []      # 存储子节点

        self.vBoxLayout = QVBoxLayout(self.view)  # 创建垂直布局

        self.setWidget(self.view)   # 设置滚动区域的部件
        self.setWidgetResizable(True)  # 设置部件可调整大小
        # 关闭水平滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 设置样式表
        self.setStyleSheet("ScrollArea{border:none;background:transparent}")
        self.view.setStyleSheet("QWidget{border:none;background:transparent}")

        self.vBoxLayout.setSpacing(5)  # 设置布局间距
        self.vBoxLayout.setContentsMargins(5, 8, 5, 8)  # 设置布局边距

        # 添加节点到菜单
        for child in tree.treeChildren:
            node = child.clone()  # 克隆节点
            node.expanded.connect(self._adjustViewSize)  # 连接展开信号

            self.treeChildren.append(node)  # 添加到子节点列表
            self.vBoxLayout.addWidget(node)  # 添加到布局

        self._initNode(self)  # 初始化节点
        self._adjustViewSize(False)  # 调整视图大小，不发出信号

    def _initNode(self, root: NavigationTreeWidget):
        """ 初始化节点，内部方法
        
        Parameters
        ----------
        root: NavigationTreeWidget
            要初始化的根节点
        """
        for c in root.treeChildren:
            c.nodeDepth -= 1  # 减小节点深度
            c.setCompacted(False)  # 设置为非紧凑模式

            if c.isLeaf():
                c.clicked.connect(self.window().fadeOut)  # 叶节点点击时淡出窗口

            self._initNode(c)  # 递归初始化子节点

    def _adjustViewSize(self, emit=True):
        """ 调整视图大小，内部方法
        
        Parameters
        ----------
        emit: bool, optional
            是否发出展开信号，默认为True
        """
        w = self._suitableWidth()  # 计算合适的宽度

        # 调整节点的宽度
        for node in self.visibleTreeNodes():
            node.setFixedWidth(w - 10)
            node.itemWidget.setFixedWidth(w - 10)

        self.view.setFixedSize(w, self.view.sizeHint().height())  # 设置视图大小

        # 限制高度不超过父窗口高度减去边距
        h = min(self.window().parent().height() - 48, self.view.height())

        self.setFixedSize(w, h)  # 设置滚动区域大小

        if emit:
            self.expanded.emit()  # 发出展开信号

    def _suitableWidth(self):
        """ 计算合适的宽度，内部方法
        
        Returns
        -------
        int
            合适的宽度值
        """
        w = 0

        # 找出所有可见节点中宽度最大的值
        for node in self.visibleTreeNodes():
            if not node.isHidden():
                w = max(w, node.suitableWidth() + 10)

        window = self.window().parent()  # 获取父窗口
        # 返回不超过父窗口宽度一半减去边距的值
        return min(window.width() // 2 - 25, w) + 10

    def visibleTreeNodes(self):
        """ 获取所有可见的树节点
        
        Returns
        -------
        list
            可见节点的列表
        """
        nodes = []
        queue = deque()
        queue.extend(self.treeChildren)

        # 使用广度优先搜索遍历所有可见节点
        while queue:
            node = queue.popleft()  # 取出队列中的第一个节点
            nodes.append(node)      # 添加到结果列表
            # 将可见的子节点添加到队列
            queue.extend([i for i in node.treeChildren if not i.isHidden()])

        return nodes