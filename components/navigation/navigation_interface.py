# coding:utf-8
from typing import Union

from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QResizeEvent, QIcon
from PyQt5.QtWidgets import QWidget

from .navigation_panel import NavigationPanel, NavigationItemPosition, NavigationWidget, NavigationDisplayMode
from .navigation_widget import NavigationTreeWidget
from common.icon import FluentIconBase


class NavigationInterface(QWidget):
    """ 导航界面组件，继承自QWidget，用于管理应用程序的导航菜单
    支持添加导航项、自定义部件、分隔线，可折叠/展开，切换显示模式 """

    displayModeChanged = pyqtSignal(NavigationDisplayMode)  # 显示模式变化信号，发射新的显示模式（如展开/折叠）

    def __init__(self, parent=None,collapsible=True):
        """ 初始化导航界面
        :param parent: QWidget - 父部件（默认为None）
        :param collapsible: bool - 是否允许面板折叠/展开（默认True）
        """
        super().__init__(parent=parent)

        self.panel = NavigationPanel(self)  # 创建导航面板核心部件（父部件为当前导航界面）
        
        self.panel.setCollapsible(collapsible)  # 设置面板是否可折叠
        
        self.panel.displayModeChanged.connect(self.displayModeChanged)  # 连接面板的显示模式变化信号到当前界面的同名信号（转发信号）

        self.resize(48, self.height())  # 初始大小：宽度48px（折叠状态），高度与父部件一致
        self.setMinimumWidth(48)  # 设置最小宽度为48px（确保折叠状态有足够空间）
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置部件背景透明（允许自定义背景效果）

    def addItem(self, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, index: int = -1,onClick=None,
                selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None,parentRouteKey: str = None) -> NavigationTreeWidget:
        
        # 调用导航面板的insertItem方法插入导航项，返回创建的部件实例
        w = self.panel.insertItem(index, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)
        
        self.setMinimumHeight(self.panel.layoutMinHeight()) # 根据面板布局的最小高度调整当前界面的最小高度（确保所有导航项可见）

        return w 

    def addWidget(self, routeKey: str, widget: NavigationWidget, index: int = -1,onClick=None, position=NavigationItemPosition.BOTTOM,
                  tooltip: str = None, parentRouteKey: str = None):
       
        # 调用panel的insertWidget方法添加自定义部件，索引-1表示追加到末尾
        self.panel.insertWidget(index, routeKey, widget, onClick, position, tooltip, parentRouteKey)
        
        self.setMinimumHeight(self.panel.layoutMinHeight()) # 根据面板布局的最小高度调整当前界面的最小高度
        
    def addSeparator(self, index: int = -1, position=NavigationItemPosition.TOP):
        """ 添加分隔线（用于视觉分隔不同组的导航项）"""

        self.panel.insertSeparator(index, position)  # 调用面板的insertSeparator方法插入分隔线
        self.setMinimumHeight(self.panel.layoutMinHeight())  # 调整界面最小高度以适应分隔线

  
    def removeWidget(self, routeKey: str):
        """ 根据routeKey从导航面板移除导航项或自定义部件 """
        self.panel.removeWidget(routeKey)  # 调用面板的removeWidget方法移除指定routeKey的部件

    def setCurrentItem(self, name: str):
        """ 设置当前选中的导航项（高亮显示）"""
        self.panel.setCurrentItem(name)  # 调用面板的setCurrentItem方法设置选中项

    def expand(self, useAni=True):
        """ 展开导航面板（从折叠状态切换到展开状态，显示完整文本和图标）
        :param useAni: bool - 是否使用动画效果（True表示启用平滑过渡，默认True）
        """
        self.panel.expand(useAni)  # 调用面板的expand方法展开面板

    def toggle(self):
        """ 切换导航面板状态（展开↔折叠） """
        self.panel.toggle() 

    def setExpandWidth(self, width: int):
        """ 设置导航面板展开状态时的宽度
        :param width: int - 展开状态宽度（像素，如200）
        """
        self.panel.setExpandWidth(width)  # 调用面板的setExpandWidth方法设置宽度

    def setMinimumExpandWidth(self, width: int):
        """ 设置允许面板展开的最小窗口宽度（窗口宽度小于此值时无法展开）
        :param width: int - 最小窗口宽度（像素，如600）
        """
        self.panel.setMinimumExpandWidth(width)  # 调用面板的setMinimumExpandWidth方法设置最小宽度


    def setCollapsible(self, collapsible: bool):
        """ 设置导航面板是否允许折叠/展开
        :param collapsible: bool - True表示可折叠，False表示固定展开状态
        """
        self.panel.setCollapsible(collapsible)


    def widget(self, routeKey: str):
        """ 根据routeKey获取导航项或自定义部件
        :param routeKey: str - 导航项/部件的唯一标识键
        :return: QWidget - 对应的部件实例（不存在则返回None）
        """
        return self.panel.widget(routeKey)  # 调用面板的widget方法获取部件

    def eventFilter(self, obj, e: QEvent):
        """ 事件过滤器：处理导航面板的事件（如尺寸变化）
        :param obj: QObject - 事件发送者对象
        :param e: QEvent - 事件对象（包含事件类型和详细信息）
        :return: bool - True表示事件已处理（不再传播），False表示未处理（继续传播）
        """
        # 仅处理导航面板的调整大小事件
        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        # 当面板显示模式不是菜单模式（如展开/折叠模式）时处理尺寸变化
        if self.panel.displayMode != NavigationDisplayMode.MENU:
            event = QResizeEvent(e)  # 将事件转换为调整大小事件
            # 若面板宽度发生变化（如展开/折叠），同步调整当前界面宽度
            if event.oldSize().width() != event.size().width(): 
                self.setFixedWidth(event.size().width())  # 设置当前界面宽度为面板新宽度

        return super().eventFilter(obj, e)  # 调用父类事件过滤方法

    def resizeEvent(self, e: QResizeEvent):
        """ 调整大小事件处理：当当前界面高度变化时，同步调整导航面板高度
        :param e: QResizeEvent - 调整大小事件对象（包含新旧尺寸信息）
        """

        # 若界面高度发生变化（宽度变化不处理），设置面板高度与界面一致
        if e.oldSize().height() != self.height():
            self.panel.setFixedHeight(self.height())
