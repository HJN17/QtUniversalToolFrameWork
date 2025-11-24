# coding:utf-8
from typing import Union
import sys 

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel


from common.config import qconfig 
from common.router import qrouter
from common.color import ThemeBackgroundColor
from common.icon import FluentIconBase 
from common.style_sheet import FluentStyleSheet
from common.animation import BackgroundAnimation 

from qframelesswindow import FramelessWindow,TitleBar, TitleBarBase
from components.navigation import (NavigationInterface, NavigationItemPosition,
                                     NavigationTreeWidget) 
from components.window.stacked_widget import StackedWidget 

class FluentWindowBase(BackgroundAnimation, FramelessWindow):
    """ 自定义Fluent风格窗口基类 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.stackedWidget = StackedWidget(self) 
        
        self._init_ui()

    def _init_ui(self):
        """ 初始化UI组件 """

        self.hBoxLayout = QHBoxLayout(self) 
        self.hBoxLayout.setSpacing(0) 
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

       
    def switchTo(self, interface: QWidget):
        self.stackedWidget.setCurrentWidget(interface, popOut=False)

    def _onCurrentInterfaceChanged(self, index: int):
        """ 当前子界面索引变化时触发（堆叠窗口切换页面） """
        widget = self.stackedWidget.widget(index)  # 获取索引对应的子界面控件
        qrouter.push(self.stackedWidget, widget.objectName())

    def _normalBackgroundColor(self):
        return ThemeBackgroundColor.color()


    def paintEvent(self, e):
        """ 窗口绘制事件（绘制背景色） """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRect(self.rect())


    def setTitleBar(self, titleBar):
        """ 设置自定义标题栏 """
        super().setTitleBar(titleBar)

        # 在macOS上隐藏自定义标题栏按钮（使用系统标题栏按钮）
        if sys.platform == "darwin" and self.isSystemButtonVisible() and isinstance(titleBar, TitleBarBase):
            titleBar.minBtn.hide() 
            titleBar.maxBtn.hide() 
            titleBar.closeBtn.hide()

class FluentTitleBar(TitleBar):
    """ 自定义Fluent风格标题栏 """

    def __init__(self, parent):
        super().__init__(parent) 
        self.setFixedHeight(48)
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # 添加窗口图标标签
        self.iconLabel = QLabel(self)  # 创建图标标签控件
        self.iconLabel.setFixedSize(18, 18)  # 设置图标固定大小18x18像素
        # 将图标标签插入到布局最左侧：索引0，对齐方式为左对齐+垂直居中
        self.hBoxLayout.insertWidget(0, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        # 连接窗口图标变化信号到setIcon方法（窗口图标更新时同步标签）
        self.window().windowIconChanged.connect(self.setIcon)

        # 添加标题标签
        self.titleLabel = QLabel(self)  # 创建标题文本标签
        # 将标题标签插入到图标标签右侧：索引1，对齐方式为左对齐+垂直居中
        self.hBoxLayout.insertWidget(1, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')  # 设置对象名为'titleLabel'（用于样式表选择）
        # 连接窗口标题变化信号到setTitle方法（窗口标题更新时同步标签）
        self.window().windowTitleChanged.connect(self.setTitle)

        # 创建垂直布局用于放置系统按钮（最小化/最大化/关闭）
        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()  # 水平布局管理按钮
        self.buttonLayout.setSpacing(0)  # 按钮间距设为0
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)  # 按钮布局边距设为0
        self.buttonLayout.setAlignment(Qt.AlignTop)  # 按钮靠上对齐
        # 将系统按钮添加到按钮布局
        self.buttonLayout.addWidget(self.minBtn)
        self.buttonLayout.addWidget(self.maxBtn)
        self.buttonLayout.addWidget(self.closeBtn)
        self.vBoxLayout.addLayout(self.buttonLayout)  # 按钮布局添加到垂直布局
        self.vBoxLayout.addStretch(1)  # 垂直布局底部添加伸缩项（按钮靠上显示）
        self.hBoxLayout.addLayout(self.vBoxLayout, 0)  # 将垂直布局添加到标题栏主布局

        #FluentStyleSheet.FLUENT_WINDOW.apply(self)  # 为标题栏应用Fluent窗口样式表

    def setTitle(self, title):
        """ 更新标题标签文本并调整大小 """
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()  # 根据文本内容自动调整标签大小

    def setIcon(self, icon):
        """ 更新图标标签：将图标缩放到18x18像素 """
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))

class FluentWindow(FluentWindowBase):
    """ 自定义Fluent窗口 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitleBar(FluentTitleBar(self))
       
        # 创建导航界面
        self.navigationInterface = NavigationInterface(self) # 创建导航界面
        self.widgetLayout = QHBoxLayout() # 创建主布局，用于放置导航界面和堆叠窗口

        # 初始化主布局
        self.hBoxLayout.addWidget(self.navigationInterface)  # 添加导航界面到主布局
        self.hBoxLayout.addLayout(self.widgetLayout)  # 添加widgetLayout到主布局
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1)  # 设置widgetLayout伸缩因子为1（占满剩余空间）

        self.widgetLayout.addWidget(self.stackedWidget)  # 将堆叠窗口添加到widgetLayout
        self.widgetLayout.setContentsMargins(0, 48, 8, 8)  # 设置边距：上48（避开标题栏高度），其他0

        # 导航界面显示模式变化时，将标题栏置于顶层（避免被遮挡）
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)
        self.titleBar.raise_()  # 确保标题栏初始在顶层

        FluentStyleSheet.FLUENT_WINDOW.apply(self)  # 为堆叠窗口应用Fluent窗口样式表


    def addSubInterface(self, interface: QWidget, icon: Union[FluentIconBase, QIcon, str], text: str,
                        position=NavigationItemPosition.TOP, parent=None, isTransparent=False) -> NavigationTreeWidget:
        
        """
        添加子界面到窗口（包含导航项）
        :param interface: 子界面（QWidget）
        :param icon: 导航项图标（FluentIconBase、QIcon或字符串）
        :param text: 导航项文本（字符串）
        :param position: 导航项位置（顶部/滚动区/底部）
        :param parent: 父导航项（用于嵌套导航）
        :param isTransparent: 是否透明背景（布尔值）
        :return: 创建的导航项（NavigationTreeWidget）
        """
       # 添加子界面到窗口（包含导航项）
        if not interface.objectName():  # 检查界面objectName是否为空（必须设置，用于导航匹配）
            raise ValueError("The object name of `interface` can't be empty string.")
        if parent and not parent.objectName():  # 检查父界面objectName是否为空（如提供父项）
            raise ValueError("The object name of `parent` can't be empty string.")

        # 设置界面的"isStackedTransparent"属性（控制堆叠窗口背景是否透明）
        interface.setProperty("isStackedTransparent", isTransparent)
        self.stackedWidget.addWidget(interface)  # 将界面添加到堆叠窗口

        # 添加导航项
        routeKey = interface.objectName()  # 路由键=界面objectName（唯一标识）
        item = self.navigationInterface.addItem(
            routeKey=routeKey,  # 路由键（用于导航匹配）
            icon=icon,  # 导航项图标
            text=text,  # 导航项文本
            onClick=lambda: self.switchTo(interface),  # 点击时切换到当前界面
            position=position,  # 导航项位置（顶部/滚动区/底部）
            tooltip=text,  # 鼠标悬停提示文本
            parentRouteKey=parent.objectName() if parent else None  # 父导航项路由键（嵌套导航）
        )

        # 初始化选中项（当添加第一个界面时）
        if self.stackedWidget.count() == 1:
            # 连接堆叠窗口当前索引变化信号到_onCurrentInterfaceChanged
            self.stackedWidget.currentChanged.connect(self._onCurrentInterfaceChanged)
            self.navigationInterface.setCurrentItem(routeKey)
            qrouter.push(self.stackedWidget, routeKey)  # 设置默认路由键


        return item  # 返回创建的导航项

    def resizeEvent(self, e):
        self.titleBar.move(15, 0)
        self.titleBar.resize(self.width()-15, self.titleBar.height())
