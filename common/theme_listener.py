# coding:utf-8
from PyQt5.QtCore import QThread
from .config import Theme, qconfig
import darkdetect # 导入darkdetect库，用于检测系统主题（深色/浅色模式）

class SystemThemeListener(QThread):
    """ 系统主题监听器线程类，继承自QThread """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def run(self):
        darkdetect.listener(self._onThemeChanged)

    def _onThemeChanged(self, theme: str):
        
        theme = Theme.DARK if theme.lower() == "dark" else Theme.LIGHT

        if qconfig.themeMode.value != Theme.AUTO or theme == qconfig.theme:
            return

        qconfig.theme = Theme.AUTO
        qconfig._cfg.themeChanged.emit(Theme.AUTO)
       