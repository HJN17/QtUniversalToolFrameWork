# coding:utf-8
from PyQt5.QtCore import QThread
from .config import Theme, qconfig
import darkdetect   # 导入darkdetect库，用于检测系统主题（深色/浅色模式）


class SystemThemeListener(QThread):
    """ 
    系统主题监听器线程类，继承自QThread
    
    功能：持续监听操作系统的主题变化（深色/浅色模式切换），
         当检测到变化时更新全局配置并发送主题变更信号
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def run(self):
        # 线程启动时执行的入口方法，通过darkdetect库注册主题变化回调函数
        # 当系统主题变化时，会自动调用_onThemeChanged方法
        darkdetect.listener(self._onThemeChanged)

    def _onThemeChanged(self, theme: str):
        """ 
        系统主题变化时的回调函数
        
        参数:
            theme: str - darkdetect返回的主题字符串，可能为"Dark"或"Light"
        """

        theme = Theme.DARK if theme.lower() == "dark" else Theme.LIGHT

        # 判断是否需要处理主题变化：
        # 1. 如果全局配置的主题模式不是AUTO（即用户手动设置了固定主题），则不处理
        # 2. 如果检测到的主题与当前配置的主题相同，也不处理
        if qconfig.themeMode.value != Theme.AUTO or theme == qconfig.theme:
            return

        qconfig.theme = Theme.AUTO
        qconfig._cfg.themeChanged.emit(Theme.AUTO)
       