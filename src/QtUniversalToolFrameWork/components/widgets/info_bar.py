# coding:utf-8
from enum import Enum
import sys
from typing import Union
import weakref

from PyQt5.QtCore import (Qt, QEvent, QSize, QRectF, QObject, QPropertyAnimation,
                          QEasingCurve, QTimer, pyqtSignal, QParallelAnimationGroup, QPoint)
from PyQt5.QtGui import QPainter, QIcon, QColor
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect, QApplication)

from ...common.auto_wrap import TextWrap
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.icon import FluentIconBase, Theme, isDarkTheme,drawIcon
from ...common.icon import FluentIcon as FIF

from ..widgets.button import TransparentToolButton


class InfoBarIcon(FluentIconBase, Enum):
    """ 信息栏图标枚举类，定义信息栏支持的图标类型 """

    INFORMATION = "Info"       # 信息类型图标
    SUCCESS = "Success"        # 成功类型图标
    WARNING = "Warning"        # 警告类型图标
    ERROR = "Error"            # 错误类型图标

    def path(self, theme=Theme.AUTO):
        """
        获取图标路径（根据主题自动切换明暗模式图标）
        
        参数:
            theme: Theme枚举，指定主题模式（AUTO/light/dark）
            
        返回:
            str: 对应主题的SVG图标文件路径
        """
        if theme == Theme.AUTO:
            # 自动模式下，根据当前系统主题判断使用深色还是浅色图标
            color = "dark" if isDarkTheme() else "light"
        else:
            # 手动指定主题时，直接使用对应主题值
            color = theme.value.lower()

        # 返回拼接后的图标路径（基于资源文件）
        return f':/resource/images/info_bar/{self.value}_{color}.svg'


class InfoBarPosition(Enum):
    """ 信息栏位置枚举类，定义信息栏在父窗口中的显示位置 """
    TOP = 0                     # 顶部居中
    BOTTOM = 1                  # 底部居中
    TOP_LEFT = 2                # 左上角
    TOP_RIGHT = 3               # 右上角
    BOTTOM_LEFT = 4             # 左下角
    BOTTOM_RIGHT = 5            # 右下角
    NONE = 6                    # 无预设位置（自定义定位）


class InfoIconWidget(QWidget):
    """ 信息栏图标部件，用于在信息栏中显示指定图标 """

    def __init__(self, icon: InfoBarIcon, parent=None):
        """
        初始化图标部件
        
        参数:
            icon: InfoBarIcon枚举，指定要显示的图标类型
            parent: QWidget，父部件
        """
        super().__init__(parent=parent)
        self.setFixedSize(36, 36)  # 设置部件固定大小为36x36像素
        self.icon = icon            # 保存图标类型

    def paintEvent(self, e):
        """
        重写绘制事件，绘制图标
        
        参数:
            e: QPaintEvent，绘制事件对象
        """
        painter = QPainter(self)    # 创建画家对象
        # 设置画家渲染提示：抗锯齿和平滑像素变换
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # 定义图标绘制区域（矩形）：x=10, y=10, 宽=15, 高=15
        rect = QRectF(10, 10, 15, 15)
        if self.icon != InfoBarIcon.INFORMATION:
            # 非信息类型图标，直接绘制
            drawIcon(self.icon, painter, rect)
        else:
            # 信息类型图标，使用主题色填充（indexes=[0]指定SVG中需要填充的路径索引）
            drawIcon(self.icon, painter, rect, indexes=[0], fill=themeColor().name())


class InfoBar(QFrame):
    """ 信息提示栏部件，用于显示通知、警告、错误等提示信息 """

    closedSignal = pyqtSignal()  # 信息栏关闭时发出的信号
    _desktopView = None          # 桌面级信息栏容器（静态变量）

    def __init__(self, icon: Union[InfoBarIcon, FluentIconBase, QIcon, str], title: str, content: str,
                 orient=Qt.Horizontal, isClosable=True, duration=1000, position=InfoBarPosition.TOP_RIGHT,
                 parent=None):
        
        super().__init__(parent=parent)
        self.title = title           
        self.content = content          
        self.orient = orient            
        self.icon = icon              
        self.duration = duration        
        self.isClosable = isClosable    
        self.position = position     

        self.titleLabel = QLabel(self)  
        self.contentLabel = QLabel(self) 
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.iconWidget = InfoIconWidget(icon) 

        self.hBoxLayout = QHBoxLayout(self)   
        self.textLayout = QHBoxLayout() if self.orient == Qt.Horizontal else QVBoxLayout()

        self.opacityEffect = QGraphicsOpacityEffect(self)  # 透明度效果对象
        self.opacityAni = QPropertyAnimation(self.opacityEffect, b'opacity', self)

        self.lightBackgroundColor = None  
        self.darkBackgroundColor = None 

        self.__initWidget()  # 初始化界面部件

    def __initWidget(self):
        """ 初始化界面部件（设置透明度、按钮样式、布局等） """
        self.opacityEffect.setOpacity(1) 
        self.setGraphicsEffect(self.opacityEffect)  # 为部件应用透明度效果

        self.closeButton.setFixedSize(36, 36)   
        self.closeButton.setIconSize(QSize(12, 12)) 
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.setVisible(self.isClosable) 

        self.__setQss()  
        self.__initLayout() 

        self.closeButton.clicked.connect(self.close)  

    def __initLayout(self):
        """ 初始化布局（设置边距、间距、添加部件到布局） """
        self.hBoxLayout.setContentsMargins(6, 6, 6, 6) 
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize) 
        self.textLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize) 
        self.textLayout.setAlignment(Qt.AlignTop) 
        self.textLayout.setContentsMargins(1, 8, 0, 8) 

        self.hBoxLayout.setSpacing(0) 
        self.textLayout.setSpacing(5)  

        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignTop | Qt.AlignLeft)

        self.textLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)

        self.titleLabel.setVisible(bool(self.title)) # 标题标签是否可见（根据是否有标题文本）

        if self.orient == Qt.Horizontal:
            self.textLayout.addSpacing(7)

        self.textLayout.addWidget(self.contentLabel, 1, Qt.AlignTop)
        self.contentLabel.setVisible(bool(self.content)) # 内容标签是否可见（根据是否有内容文本）
        self.hBoxLayout.addLayout(self.textLayout) 


        self.hBoxLayout.addSpacing(12)  # 主布局添加12像素间距
        # 添加关闭按钮到主布局（顶部左对齐）
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignLeft)

        self._adjustText()  # 调整文本显示（自动换行）

    def __setQss(self):
        """ 设置样式表（通过对象名和属性让样式表生效） """
        self.titleLabel.setObjectName('titleLabel')    # 设置标题标签对象名（用于QSS选择）
        self.contentLabel.setObjectName('contentLabel')  # 设置内容标签对象名
        if isinstance(self.icon, Enum):
            # 如果图标是枚举类型，设置type属性为枚举值（用于QSS根据类型设置不同样式）
            self.setProperty('type', self.icon.value)

        FluentStyleSheet.INFO_BAR.apply(self)  # 应用信息栏样式表

    def __fadeOut(self):
        """ 淡出动画（信息栏关闭前的渐隐效果） """
        self.opacityAni.setDuration(200)  # 动画时长200毫秒
        self.opacityAni.setStartValue(1)  # 起始透明度1（不透明）
        self.opacityAni.setEndValue(0)    # 结束透明度0（完全透明）
        self.opacityAni.finished.connect(self.close)  # 动画结束后关闭部件
        self.opacityAni.start()  # 启动动画

    def _adjustText(self):
        """ 调整文本显示（自动换行，限制最大宽度） """
        w = 900 if not self.parent() else (self.parent().width() - 50)

        chars = max(min(w / 10, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])

        chars = max(min(w / 9, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.adjustSize() # 调整部件大小以适应文本内容


    def setCustomBackgroundColor(self, light, dark):
        self.lightBackgroundColor = QColor(light)  # 转换为QColor并保存
        self.darkBackgroundColor = QColor(dark)
        self.update()  # 触发重绘以应用新背景色

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            # 父部件调整大小或窗口状态变化时，重新调整文本
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                self._adjustText()

        return super().eventFilter(obj, e)  # 调用父类实现

    def closeEvent(self, e):
       
        self.closedSignal.emit()  # 发出关闭信号
        self.deleteLater()  # 安排部件延迟删除（释放资源）
        e.ignore()  # 忽略事件（由deleteLater处理）

    def showEvent(self, e):

        self._adjustText()  # 显示前调整文本
        super().showEvent(e)  # 调用父类显示事件

        # 显示时长>=0时，启动定时器，到时后执行淡出动画
        if self.duration >= 0:
            QTimer.singleShot(self.duration, self.__fadeOut) # 启动定时器，到时后执行淡出动画

        # 非NONE位置时，通过InfoBarManager管理位置和动画
        if self.position != InfoBarPosition.NONE:
            manager = InfoBarManager.make(self.position)
            manager.add(self)

        if self.parent():
            self.parent().installEventFilter(self)

    def paintEvent(self, e):

        super().paintEvent(e) 

        if self.lightBackgroundColor is None:
            return 

        painter = QPainter(self) 
        painter.setRenderHints(QPainter.Antialiasing)  
        painter.setPen(Qt.NoPen)

        if isDarkTheme():
            painter.setBrush(self.darkBackgroundColor)
        else:
            painter.setBrush(self.lightBackgroundColor)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 6, 6) 

    @classmethod
    def new(cls, icon, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
            position=InfoBarPosition.TOP_RIGHT, parent=None):
       
        w = InfoBar(icon, title, content, orient, isClosable, duration, position, parent)
        w.show()  
        return w

    @classmethod
    def info(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
             position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建信息类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.INFORMATION, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def success(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建成功类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.SUCCESS, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def warning(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建警告类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.WARNING, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def error(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
              position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建错误类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.ERROR, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def desktopView(cls):
        """
        获取桌面级信息栏容器（静态方法）
        
        返回:
            DesktopInfoBarView: 桌面级容器实例（用于在桌面显示信息栏）
        """
        if not cls._desktopView:
            cls._desktopView = DesktopInfoBarView()
            cls._desktopView.show()  # 首次调用时创建并显示容器

        return cls._desktopView

class InfoBarManager(QObject):
 
    _instance = None
    managers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InfoBarManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance.__initialized = False

        return cls._instance

    def __init__(self):
        super().__init__()
        if self.__initialized:
            return

        self.margin_x = 18
        self.margin_y = 54
        self.slideAnis = []  # 只保留滑动动画列表
        self.__initialized = True

    def add(self, infoBar: InfoBar):
        p = infoBar.parent()    # type:QWidget
        if not p:
            return

        slideAni = self._createSlideAni(infoBar)
        self.slideAnis.append(slideAni)

        infoBar.setProperty('slideAni', slideAni)

        slideAni.start()

        #动画结束时，从列表移除
        slideAni.finished.connect(lambda: self.slideAnis.remove(slideAni))

      
    def _createSlideAni(self, infoBar: InfoBar):
        slideAni = QPropertyAnimation(infoBar, b'pos')
        slideAni.setEasingCurve(QEasingCurve.OutQuad)
        slideAni.setDuration(200)

        slideAni.setStartValue(self._slideStartPos(infoBar))
        slideAni.setEndValue(self._pos(infoBar))

        return slideAni

    
    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        raise NotImplementedError

    def _slideStartPos(self, infoBar: InfoBar) -> QPoint:
        raise NotImplementedError

    

    @classmethod
    def register(cls, name):
       
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def make(cls, position: InfoBarPosition):
        if position not in cls.managers:
            raise ValueError(f'`{position}` is an invalid animation type.')

        return cls.managers[position]()


@InfoBarManager.register(InfoBarPosition.TOP_RIGHT)
class TopRightInfoBarManager(InfoBarManager):
    """ 右上角位置信息栏管理器（信息栏右上角垂直堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:

        p = infoBar.parent()
        parentSize = parentSize or p.size()
        
        x = parentSize.width() - infoBar.width() - self.margin_x
        y = self.margin_y

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：父部件右侧（从右往左滑入）"""
        return QPoint(infoBar.parent().width(), self._pos(infoBar).y())


class DesktopInfoBarView(QWidget):
    """ 桌面级信息栏容器（用于在桌面显示信息栏，不受应用窗口限制） """

    def __init__(self, parent=None):
        super().__init__(parent)

        if sys.platform == "win32":
            # Windows系统：无边框、置顶、子窗口（避免任务栏显示）
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        else:
            # 其他系统：无边框、置顶、工具窗口、鼠标穿透
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 鼠标事件穿透（点击穿透到桌面）
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明
        # 设置窗口大小为屏幕可用区域（覆盖整个桌面）
        self.setGeometry(QApplication.primaryScreen().availableGeometry())
