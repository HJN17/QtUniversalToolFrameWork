# coding: utf-8
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from common.config import qconfig
from common.icon import FluentIcon as FIF,Icon
from common.theme_listener import SystemThemeListener

from components.window import FluentWindow, SplashScreen
from components.navigation import NavigationInterface, NavigationItemPosition

from resources import resource

from view.home_interface import HomeInterface
from view.setting_interface import SettingInterface
from view.image_view_interface import ImageViewInterface

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__() 
        self.initWindow()

        self.themeListener = SystemThemeListener(self) # 创建系统主题监听器(用于监听系统主题变化并同步应用主题)

        self.homeInterface = HomeInterface(self)
        self.imageViewInterface = ImageViewInterface(self)
        self.settingInterface = SettingInterface(self)

        self.initNavigation()
        QTimer.singleShot(100, self.splashScreen.finish)  # 2000毫秒后调用finish方法结束启动屏显示
        self.themeListener.start()

    def initNavigation(self):
        """ 初始化导航栏，添加导航项和分隔符 """
        
        self.addSubInterface(self.homeInterface, FIF.HOME,'首页')
        self.navigationInterface.addSeparator()  # 在导航栏添加分隔线
    
        pos = NavigationItemPosition.SCROLL # 后续导航项位置设为滚动区

        self.addSubInterface(self.imageViewInterface, FIF.PHOTO,'图像工具',pos)

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM) # 在导航栏底部添加设置界面

    def initWindow(self):
        self.resize(980, 780)
        self.setMinimumWidth(860)
        self.setWindowIcon(QIcon(':/resource/images/logo.png'))
        self.setWindowTitle('FrameCoreTool')

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(128, 128))
        self.splashScreen.raise_() # 将启动屏提升到顶层显示

        desktop = QApplication.desktop().availableGeometry() # 获取桌面可用区域尺寸
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())  # 将启动屏大小调整为窗口当前大小

    def closeEvent(self, e):
        """
        处理窗口关闭事件

        :param e: 窗口关闭事件对象(QCloseEvent)，可调用accept()/ignore()控制是否关闭
        """
        self.themeListener.terminate()  # 终止主题监听器线程
        self.themeListener.deleteLater()  # 安排主题监听器对象稍后删除(释放资源)
        super().closeEvent(e)
