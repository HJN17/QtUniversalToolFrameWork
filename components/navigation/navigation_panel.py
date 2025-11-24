# coding:utf-8
from enum import Enum
from typing import Union

from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize, QEvent, QEasingCurve, pyqtSignal, QPoint
from PyQt5.QtGui import QResizeEvent, QIcon, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication, QHBoxLayout

from .navigation_widget import (NavigationTreeWidgetBase, NavigationToolButton, NavigationWidget, NavigationSeparator,
                                NavigationTreeWidget, NavigationFlyoutMenu)
from ..widgets.acrylic_label import AcrylicBrush
from ..widgets.scroll_area import ScrollArea
from ..widgets.tool_tip import ToolTipFilter
from ..widgets.scroll_bar import ScrollBarHandleDisplayMode
from ..widgets.flyout import Flyout, FlyoutAnimationType, FlyoutViewBase, SlideRightFlyoutAnimationManager
from common.style_sheet import FluentStyleSheet, isDarkTheme
from common.icon import FluentIconBase
from common.icon import FluentIcon as FIF


class NavigationDisplayMode(Enum):
    """ 导航栏显示模式枚举 """
    COMPACT = 1  # 紧凑模式（显示图标+部分文本，宽度固定）
    EXPAND = 2   # 展开模式（显示完整图标和文本，宽度自适应）
    MENU = 3     # 菜单模式（以弹出菜单形式展示，独立于主窗口）

class NavigationItemPosition(Enum):
    """ 导航项位置枚举 """
    TOP = 0      # 顶部位置（固定在导航栏顶部，不随滚动变化）
    SCROLL = 1   # 滚动区域（位于中间可滚动区域，随内容滚动）
    BOTTOM = 2   # 底部位置（固定在导航栏底部，不随滚动变化）

class NavigationToolTipFilter(ToolTipFilter):
    """ 导航工具提示过滤器（继承自基础工具提示过滤器） """

    def _canShowToolTip(self) -> bool: # 重写基础方法，添加额外条件：仅在紧凑模式下显示工具提示
        
        isVisible = super()._canShowToolTip()

        parent = self.parent() # 获取父导航项部件（通常是NavigationPanel）
        
        return isVisible and parent.isCompacted # 仅当基础可见且导航项处于紧凑模式时显示工具提示
    

class NavigationItem:
    """ 导航项数据结构（存储导航项的路由键、父路由键和对应的部件） """

    def __init__(self, routeKey: str, parentRouteKey: str, widget: NavigationWidget):
        self.routeKey = routeKey          # 导航项唯一标识键（用于路由和查找）
        self.parentRouteKey = parentRouteKey  # 父导航项路由键（用于树形结构）
        self.widget = widget              # 导航项对应的UI部件


class NavigationPanel(QFrame):
    """ 导航面板主类（继承自QFrame，实现可折叠、多模式显示的导航栏） """


    displayModeChanged = pyqtSignal(NavigationDisplayMode) # 定义显示模式改变信号，参数为导航显示模式枚举值

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent
        self._isCollapsible = True  # 是否允许折叠的标志（控制导航栏能否收缩）

        self.scrollArea = ScrollArea(self)  # 创建滚动区域控件，用于容纳可滚动的导航项
        self.scrollWidget = QWidget()  # 滚动区域的内容部件（所有可滚动导航项的容器）

        # 创建菜单按钮（使用Fluent图标库的菜单图标）和返回按钮（使用返回图标）
        self.menuButton = NavigationToolButton(FIF.MENU, self) #MENU

        # 创建导航项布局管理器：主布局、顶部布局、底部布局、滚动区域布局
        self.vBoxLayout = NavigationItemLayout(self)
        self.topLayout = NavigationItemLayout()
        self.bottomLayout = NavigationItemLayout()
        self.scrollLayout = NavigationItemLayout(self.scrollWidget)

        self.items = {}   # 存储导航项的字典（键：routeKey，值：NavigationItem对象）
    
        # 创建展开/折叠动画实例（作用于当前部件的geometry属性）
        self.expandAni = QPropertyAnimation(self, b'geometry', self) # 创建展开/折叠动画实例（作用于当前部件的geometry属性）
        self.expandWidth = 200  # 展开模式下的宽度（像素）
        self.minimumExpandWidth = 800  # 允许展开的最小窗口宽度（小于此值时自动切换为菜单模式）

        self.displayMode = NavigationDisplayMode.COMPACT # 初始化显示模式为紧凑模式

        self.__initWidget()  # 初始化UI部件（设置布局、样式、信号槽等）

    def __initWidget(self):
        self.resize(48, self.height())  # 设置初始大小：宽度48px（紧凑模式），高度与父部件一致

        self.window().installEventFilter(self)  # 为窗口安装事件过滤器（用于监听窗口大小变化、鼠标点击等事件）

        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # 禁用水平滚动条
        self.scrollArea.horizontalScrollBar().setEnabled(False) # 禁用水平滚动条的交互功能（用户无法通过拖动滚动条来滚动内容）
        self.scrollArea.setWidget(self.scrollWidget)  # 设置滚动区域的内容部件
        self.scrollArea.setWidgetResizable(True)  # 内容部件大小自适应滚动区域
        # 设置垂直滚动条的手柄显示模式：仅在鼠标悬停时显示
        self.scrollArea.scrollDelagate.vScrollBar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)

        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)  # 配置展开/折叠动画：缓动曲线为OutQuad（先快后慢），持续时间150毫秒
        self.expandAni.setDuration(150)

        self.menuButton.clicked.connect(self.toggle)
        self.expandAni.finished.connect(self._onExpandAniFinished) # finished 信号触发时调用 _onExpandAniFinished 槽函数
       

        # 为菜单按钮安装工具提示过滤器，设置提示文本为"打开导航"
        self.menuButton.installEventFilter(ToolTipFilter(self.menuButton, 500))
        self.menuButton.setToolTip("打开导航")

        self.setProperty('menu', False)  # 设置样式属性：非菜单模式；为滚动部件设置对象名（用于样式表选择）
        self.scrollWidget.setObjectName('scrollWidget')
        # 应用导航栏样式表（FluentDesign风格）
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()  # 初始化布局（将各部件添加到对应布局中）

    def __initLayout(self):
        # 设置布局边距（上、右、下、左）：主布局10px边距，其他布局4px边距
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.topLayout.setContentsMargins(4, 48, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        # 设置布局内控件间距：所有布局间距为4px
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        # 主布局添加子布局：顶部布局（比例0）、滚动区域（比例1，占满剩余空间）、底部布局（比例0）
        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addLayout(self.bottomLayout, 0)

        # 设置各布局内控件对齐方式：顶部/滚动区域居上，底部布局居下
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

        # 顶部布局添加返回按钮和菜单按钮（对齐方式：顶部）

        self.topLayout.addWidget(self.menuButton, 0, Qt.AlignTop)


    def widget(self, routeKey: str):
        """ 根据路由键获取导航项部件
        
        参数
        ----------
        routeKey: str
            导航项的唯一标识键
        
        返回值
        ----------
        NavigationWidget
            对应的导航项部件，如果路由键不存在则抛出RouteKeyError异常
        """
        if routeKey not in self.items:
            raise Exception(f"`{routeKey}` 是非法路由键（不存在）")

        return self.items[routeKey].widget

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                   selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey=None) -> NavigationTreeWidget:
        """ 插入导航树项（创建标准树形导航项并插入到指定位置）
        
        参数
        ----------
        index: int
            插入位置索引（-1表示末尾，父项为树形部件时有效）
        
        routeKey: str
            导航项的唯一标识键
        
        icon: str | QIcon | FluentIconBase
            导航项的图标
        
        text: str
            导航项的显示文本
        
        onClick: callable
            点击事件回调函数（可选）
        
        position: NavigationItemPosition
            导航项的位置（TOP/SCROLL/BOTTOM）
        
        selectable: bool
            是否允许选中状态
        
        tooltip: str
            工具提示文本（可选）
        
        parentRouteKey: str
            父导航项的路由键（父项必须是NavigationTreeWidget类型，可选）
        
        返回值
        ----------
        NavigationTreeWidget
            创建的树形导航项部件
        """
        if routeKey in self.items:
            return  # 如果路由键已存在，直接返回（避免重复添加）

        # 创建树形导航项部件（标准导航项，支持展开/折叠子项）
        w = NavigationTreeWidget(icon, text, selectable, self)
        # 插入部件到指定位置
        self.insertWidget(index, routeKey, w, onClick, position, tooltip, parentRouteKey)
        return w

    def insertWidget(self, index: int, routeKey: str, widget: NavigationWidget, onClick=None,
                     position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey: str = None):
        """ 插入自定义导航部件（将用户提供的部件插入到指定位置）
        
        参数
        ----------
        index: int
            插入位置索引（-1表示末尾）
        
        routeKey: str
            导航项的唯一标识键
        
        widget: NavigationWidget
            自定义导航部件实例
        
        onClick: callable
            点击事件回调函数（可选）
        
        position: NavigationItemPosition
            部件的位置（TOP/SCROLL/BOTTOM）
        
        tooltip: str
            工具提示文本（可选）
        
        parentRouteKey: str
            父导航项的路由键（用于树形结构，可选）
        """
        if routeKey in self.items:
            return  # 路由键已存在，直接返回

        # 注册部件到导航项字典（绑定路由键、事件、工具提示等）
        self._registerWidget(routeKey, parentRouteKey, widget, onClick, tooltip)
        if parentRouteKey:
            # 如果指定了父路由键，将部件插入到父树形部件中
            self.widget(parentRouteKey).insertChild(index, widget)
        else:
            # 否则直接插入到指定位置的布局中
            self._insertWidgetToLayout(index, widget, position)

    def insertSeparator(self, index: int, position=NavigationItemPosition.TOP):
        """ 插入分隔线（在指定位置插入视觉分隔线）
        
        参数
        ----------
        index: int
            插入位置索引（-1表示末尾）
        
        position: NavigationItemPosition
            分隔线的位置（TOP/SCROLL/BOTTOM）
        """
        separator = NavigationSeparator(self)  # 创建分隔线部件
        self._insertWidgetToLayout(index, separator, position)  # 插入到指定布局

    def _registerWidget(self, routeKey: str, parentRouteKey: str, widget: NavigationWidget, onClick, tooltip: str):
        """ 注册导航部件（内部方法，绑定事件、属性和工具提示）
        
        参数
        ----------
        routeKey: str
            导航项的唯一标识键
        
        parentRouteKey: str
            父导航项的路由键（可选）
        
        widget: NavigationWidget
            要注册的导航部件
        
        onClick: callable
            点击事件回调函数（可选）
        
        tooltip: str
            工具提示文本（可选）
        """
        # 将部件的点击信号连接到内部处理方法（_onWidgetClicked）
        widget.clicked.connect(self._onWidgetClicked)

        if onClick is not None:
            # 如果提供了自定义点击回调，额外连接
            widget.clicked.connect(onClick)

        # 为部件设置属性：路由键、父路由键（用于后续查找和树形结构）
        widget.setProperty('routeKey', routeKey)
        widget.setProperty('parentRouteKey', parentRouteKey)
        # 将部件添加到导航项字典
        self.items[routeKey] = NavigationItem(routeKey, parentRouteKey, widget)

        # 根据当前显示模式设置部件是否紧凑显示（隐藏文本/显示文本）
        if self.displayMode in [NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU]:
            widget.setCompacted(False)

        if tooltip:
            # 如果提供了工具提示，设置并安装导航工具提示过滤器（仅在紧凑模式显示）
            widget.setToolTip(tooltip)
            widget.installEventFilter(NavigationToolTipFilter(widget, 1000))

    def _insertWidgetToLayout(self, index: int, widget: NavigationWidget, position: NavigationItemPosition):
        """ 将部件插入到指定位置的布局（内部方法，处理布局添加逻辑）
        
        参数
        ----------
        index: int
            插入位置索引
        
        widget: NavigationWidget
            要插入的部件
        
        position: NavigationItemPosition
            插入位置（TOP/SCROLL/BOTTOM）
        """
        if position == NavigationItemPosition.TOP:
            # 顶部位置：父部件设为当前导航栏，添加到顶部布局
            widget.setParent(self)
            self.topLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        elif position == NavigationItemPosition.SCROLL:
            # 滚动区域：父部件设为滚动内容部件，添加到滚动布局
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        else:
            # 底部位置：父部件设为当前导航栏，添加到底部布局
            widget.setParent(self)
            self.bottomLayout.insertWidget(index, widget, 0, Qt.AlignBottom)

        widget.show()  # 显示部件

    def removeWidget(self, routeKey: str):
        """ 移除导航项（包括其子项，递归清理）
        
        参数
        ----------
        routeKey: str
            要移除的导航项路由键
        """
        if routeKey not in self.items:
            return  # 路由键不存在，直接返回

        item = self.items.pop(routeKey)  # 从字典中移除导航项

        if item.parentRouteKey is not None:
            # 如果有父项，从父树形部件中移除子项
            self.widget(item.parentRouteKey).removeChild(item.widget)

        if isinstance(item.widget, NavigationTreeWidgetBase):
            # 如果是树形部件，递归移除所有子导航项
            for child in item.widget.findChildren(NavigationWidget, options=Qt.FindChildrenRecursively):
                key = child.property('routeKey')
                if key is None:
                    continue  # 跳过无路由键的子部件

                self.items.pop(key)  # 从字典中移除子项
                child.deleteLater()  # 计划删除子部件（释放内存）

        item.widget.deleteLater()  # 计划删除当前部件

    
    def setCollapsible(self, on: bool):
        """ 设置是否允许折叠/展开
        
        参数
        ----------
        on: bool
            True：允许折叠/展开，False：禁用折叠（强制展开模式）
        """
        self._isCollapsible = on
        # 如果禁用折叠且当前不是展开模式，强制展开
        if not on and self.displayMode != NavigationDisplayMode.EXPAND:
            self.expand(False)

    def setExpandWidth(self, width: int):
        """ 设置展开模式下的宽度（最小42px，避免过窄无法显示内容）
        
        参数
        ----------
        width: int
            展开模式的宽度（像素，必须大于42）
        """
        if width <= 42:
            return  # 宽度过小，忽略设置

        self.expandWidth = width
        # 更新导航部件的展开宽度（留出10px内边距）
        NavigationWidget.EXPAND_WIDTH = width - 10

    def setMinimumExpandWidth(self, width: int):
        """ 设置允许展开的最小窗口宽度（小于此宽度时自动切换为菜单模式）
        
        参数
        ----------
        width: int
            最小窗口宽度（像素）
        """
        self.minimumExpandWidth = width

    def expand(self, useAni=True):
        """ 展开导航栏（从紧凑/最小化模式切换到展开/菜单模式）
        
        参数
        ----------
        useAni: bool
            True：使用动画过渡，False：立即切换（无动画）
        """
        self._setWidgetCompacted(False)  # 设置所有导航部件为非紧凑模式（显示文本）
        self.expandAni.setProperty('expand', True)  # 标记动画为"展开"状态
        self.menuButton.setToolTip('关闭导航')  # 更新菜单按钮工具提示

        # 根据窗口宽度判断展开模式：展开模式（窗口足够宽）或菜单模式（窗口较窄）
        expandWidth = self.minimumExpandWidth
        if (self.window().width() >= expandWidth) or not self._isCollapsible: # 解释：如果窗口宽度大于等于最小展开宽度+展开宽度-322（322是导航栏的宽度），或者禁用了折叠，那么就切换到展开模式；否则切换到菜单模式
            self.displayMode = NavigationDisplayMode.EXPAND # 切换到展开模式
        else:
            self.setProperty('menu', True)
            self.setStyle(QApplication.style()) # 刷新样式
            self.displayMode = NavigationDisplayMode.MENU 
            
            
            # 如果父部件不是窗口，将导航栏移到主窗口（确保菜单模式独立显示）
            if not self._parent.isWindow(): # 如果父部件不是窗口，将导航栏移到主窗口（确保菜单模式独立显示）
                pos = self.parent().pos() # 记录当前位置
                self.setParent(self.window()) # 将导航栏设为主窗口的子部件
                self.move(pos) # 移动到记录的位置

            self.show()  # 确保导航栏可见

        if useAni:
            # 使用动画过渡：设置起始/结束大小，启动动画
            self.displayModeChanged.emit(self.displayMode) # 触发显示模式改变信号（通知外部监听）
            self.expandAni.setStartValue(QRect(self.pos(), QSize(48, self.height())))  # 起始大小：48px宽
            self.expandAni.setEndValue(QRect(self.pos(), QSize(self.expandWidth, self.height())))  # 结束大小：展开宽度
          
            self.expandAni.start()
        else:
            # 无动画：直接调整大小并触发完成回调
            self.resize(self.expandWidth, self.height())
            self._onExpandAniFinished()

    def collapse(self):
        """ 折叠导航栏（从展开/菜单模式切换到紧凑/最小化模式） """
        if self.expandAni.state() == QPropertyAnimation.Running:
            return

        # 折叠所有树形导航项（关闭子菜单）
        for item in self.items.values():
            w = item.widget
            if isinstance(w, NavigationTreeWidgetBase) and w.isRoot():
                w.setExpanded(False)

        # 设置折叠动画：起始大小为当前大小，结束大小为48px宽（紧凑模式）
        self.expandAni.setStartValue(
            QRect(self.pos(), QSize(self.width(), self.height())))
        self.expandAni.setEndValue(
            QRect(self.pos(), QSize(48, self.height())))
        self.expandAni.setProperty('expand', False)  # 标记动画为"折叠"状态
        self.expandAni.start()

        self.menuButton.setToolTip('打开导航')  # 更新菜单按钮工具提示

    def toggle(self):
        """ 切换导航栏显示状态（展开↔折叠） """
        if self.displayMode in [NavigationDisplayMode.COMPACT]:
            self.expand()  # 当前为紧凑/最小化模式 → 展开
        else:
            self.collapse()  # 当前为展开/菜单模式 → 折叠

    def setCurrentItem(self, routeKey: str):
        """ 设置当前选中的导航项（高亮显示）
        
        参数
        ----------
        routeKey: str
            要选中的导航项路由键
        """
        if routeKey not in self.items:
            return  # 路由键不存在，直接返回

        # 遍历所有导航项，设置选中状态（仅目标项为True，其余为False）
        for k, item in self.items.items():
            item.widget.setSelected(k == routeKey)

    def _onWidgetClicked(self):
        """ 导航项点击事件处理（内部回调） """
        widget = self.sender()  # 获取触发事件的导航部件（NavigationWidget实例）
        if not widget.isSelectable:
            # 如果部件不可选中，显示弹出菜单（如非交互性按钮）
            return self._showFlyoutNavigationMenu(widget)

        # 如果可选中，设置为当前选中项并更新路由历史
        self.setCurrentItem(widget.property('routeKey'))

        # 判断是否为叶子节点（非树形部件或无子项的树形部件）
        isLeaf = not isinstance(widget, NavigationTreeWidgetBase) or widget.isLeaf()
        if self.displayMode == NavigationDisplayMode.MENU and isLeaf:
            self.collapse()  # 菜单模式下点击叶子节点后自动折叠
        elif self.isCollapsed():
            # 紧凑模式下点击，显示弹出菜单
            self._showFlyoutNavigationMenu(widget)

    def _showFlyoutNavigationMenu(self, widget: NavigationTreeWidget):
        """ 显示弹出式导航菜单（紧凑模式下点击树形部件时）
        
        参数
        ----------
        widget: NavigationTreeWidget
            触发弹出菜单的树形导航部件
        """
        # 仅在紧凑模式且部件为树形根节点（有子项）时显示
        if not (self.isCollapsed() and isinstance(widget, NavigationTreeWidget)):
            return

        if not widget.isRoot() or widget.isLeaf():
            return  # 非根节点或叶子节点不显示菜单

        layout = QHBoxLayout()  # 创建水平布局容纳菜单内容

        
        # 创建基础弹出窗口视图（用于容纳菜单内容）
        view = FlyoutViewBase()
        view.setLayout(layout)
        flyout = Flyout(view, self.window())

        # 创建弹出菜单部件（包含树形导航项的子项）
        menu = NavigationFlyoutMenu(widget, view)
        layout.setContentsMargins(0, 0, 0, 0)  # 清除布局边距
        layout.addWidget(menu)  # 添加菜单到布局

        # 执行弹出动画：调整大小并计算位置
        flyout.resize(flyout.sizeHint())
        pos = SlideRightFlyoutAnimationManager(flyout).position(widget)  # 计算弹出位置（右滑动画）
        flyout.exec(pos, FlyoutAnimationType.SLIDE_RIGHT)  # 显示弹出菜单

        # 绑定菜单展开事件：动态调整弹出菜单大小（子项展开时）
        menu.expanded.connect(lambda: self._adjustFlyoutMenuSize(flyout, widget, menu))

    def _adjustFlyoutMenuSize(self, flyout: Flyout, widget: NavigationTreeWidget, menu: NavigationFlyoutMenu):
        """ 调整弹出菜单大小（子项展开时动态适配内容）
        
        参数
        ----------
        flyout: Flyout
            弹出窗口实例
        
        widget: NavigationTreeWidget
            触发菜单的树形部件
        
        menu: NavigationFlyoutMenu
            菜单内容部件
        """
        # 设置视图大小为菜单内容大小，窗口大小为布局推荐大小
        flyout.view.setFixedSize(menu.size())
        flyout.setFixedSize(flyout.layout().sizeHint())

        # 重新计算弹出位置（确保菜单在窗口可视区域内）
        manager = flyout.aniManager
        pos = manager.position(widget)

        rect = self.window().geometry()  # 获取主窗口几何区域
        # 计算菜单最大允许尺寸（避免超出窗口边界）
        w, h = flyout.sizeHint().width() + 5, flyout.sizeHint().height()
        # 限制菜单位置在窗口内（左右不超出窗口，上下留边距）
        x = max(rect.left(), min(pos.x(), rect.right() - w))
        y = max(rect.top() + 42, min(pos.y() - 4, rect.bottom() - h + 5))
        flyout.move(x, y)  # 移动菜单到计算位置

    def isCollapsed(self):
        """ 判断导航栏是否处于折叠状态
        
        返回值
        ----------
        bool
            True：紧凑/最小化模式（折叠），False：展开/菜单模式（未折叠）
        """
        return self.displayMode == NavigationDisplayMode.COMPACT

    def eventFilter(self, obj, e: QEvent):
        """ 事件过滤器（监听窗口事件，处理自动折叠/展开逻辑）
        
        参数
        ----------
        obj: QObject
            事件源对象
        
        e: QEvent
            事件对象
        
        返回值
        ----------
        bool
            True：事件已处理，False：事件未处理（传递给其他过滤器）
        """

        

        # 仅处理主窗口事件且允许折叠时
        if obj is not self.window() or not self._isCollapsible:
            return super().eventFilter(obj, e)

        if e.type() == QEvent.MouseButtonRelease:
            # 鼠标点击窗口空白区域时，自动折叠菜单模式
            if not self.geometry().contains(e.pos()) and self.displayMode == NavigationDisplayMode.MENU:
                self.collapse()
        elif e.type() == QEvent.Resize:
            self.collapse()
            
        return super().eventFilter(obj, e)

    def _onExpandAniFinished(self):
        """ 展开/折叠动画结束回调 """
        if not self.expandAni.property('expand'):
            # 动画为"折叠"状态：恢复到紧凑/最小化模式
          
            self.displayMode = NavigationDisplayMode.COMPACT

            self.displayModeChanged.emit(self.displayMode)  # 发送显示模式变更信号

        if self.displayMode == NavigationDisplayMode.COMPACT:
            # 紧凑模式：重置菜单属性，设置导航部件为紧凑模式（隐藏文本）
            self.setProperty('menu', False)
            self.setStyle(QApplication.style())

            for item in self.items.values():
                item.widget.setCompacted(True)

            # 将导航栏移回父部件（从窗口独立状态恢复）
            if not self._parent.isWindow():
                self.setParent(self._parent)
                self.move(0, 0)
                self.show()

    def _setWidgetCompacted(self, isCompacted: bool):
        """ 设置所有导航部件的紧凑模式状态（显示/隐藏文本）
        
        参数
        ----------
        isCompacted: bool
            True：紧凑模式（仅显示图标），False：展开模式（显示图标+文本）
        """
        # 遍历所有导航部件，设置紧凑模式状态
        for item in self.findChildren(NavigationWidget):
            item.setCompacted(isCompacted)


    def layoutMinHeight(self):

        """ 计算布局的最小高度（用于自适应窗口大小）
        
        返回值
        ----------
        int
            布局所需的最小高度（像素）
        """
        th = self.topLayout.minimumSize().height()  # 顶部布局最小高度
        bh = self.bottomLayout.minimumSize().height()  # 底部布局最小高度
        # 分隔线总高度（所有分隔线高度之和）
        sh = sum(w.height() for w in self.findChildren(NavigationSeparator))
        # 布局间距总和（顶部和底部布局的控件数量×间距）
        spacing = self.topLayout.count() * self.topLayout.spacing()
        spacing += self.bottomLayout.count() * self.bottomLayout.spacing()
        # 总最小高度：36px（基础边距）+ 各部分高度 + 间距
        return 36 + th + bh + sh + spacing


    def paintEvent(self, e):
        """ 重绘事件（处理亚克力效果绘制）
        
        参数
        ----------
        e: QPaintEvent
            重绘事件对象
        """
        # 仅在可以绘制亚克力且处于菜单模式时绘制
        if self.displayMode != NavigationDisplayMode.MENU:
            return super().paintEvent(e)

        # 创建绘制路径：带圆角的矩形（菜单模式的特殊形状）
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)  # 设置填充规则为缠绕填充
        # 添加圆角矩形（左上角和右上角圆角7px，底部直角）
        path.addRoundedRect(0, 1, self.width() - 1, self.height() - 1, 7, 7)
        path.addRect(0, 1, 8, self.height() - 1)  # 左侧添加矩形（覆盖圆角，形成直边）
       

        super().paintEvent(e)  # 调用父类重绘（绘制子部件等）


class NavigationItemLayout(QVBoxLayout):
    """ 导航项布局（继承自QVBoxLayout，优化导航项排列） """

    def setGeometry(self, rect: QRect):
        """ 重写布局几何设置（确保导航项垂直居中对齐）"""
        super().setGeometry(rect)
        # 遍历所有布局项，调整分隔线位置（确保垂直居中）
        for i in range(self.count()):
            item = self.itemAt(i)
            if isinstance(item.widget(), NavigationSeparator):
                geo = item.geometry()  # 获取分隔线当前几何区域
                # 重新设置分隔线位置：宽度充满布局，垂直居中
                item.widget().setGeometry(0, geo.y(), rect.width(), geo.height())
