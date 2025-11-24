# coding:utf-8

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QStackedWidget 


class StackedRouter(QObject):
    """ 路由管理器 - 管理多个堆栈窗口部件的路由历史，提供页面跳转功能 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.history = {}

    def push(self, stacked: QStackedWidget, routeKey: str):
        
        self.history[routeKey] = stacked

    def pop(self):

        if not self.history: 
            return

        self.history.popitem() 

    def remove(self, routeKey: str):
      
        if routeKey in self.history:
            del self.history[routeKey]

       

qrouter = StackedRouter()