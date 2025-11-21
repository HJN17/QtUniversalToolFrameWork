# coding:utf-8
# 导入必要的类型提示和工具
from typing import Dict, List  # Dict: 字典类型提示, List: 列表类型提示
from itertools import groupby  # groupby: 用于对序列进行分组去重

# 导入PyQt5相关模块
from PyQt5.QtCore import QObject, pyqtSignal  # Qt: Qt常量, QObject: 所有Qt对象的基类, pyqtSignal: 信号类
from PyQt5.QtWidgets import QWidget, QStackedWidget  # QWidget: 所有用户界面对象的基类, QStackedWidget: 堆栈式窗口部件


class RouteItem:
    """ 路由项 - 封装堆栈窗口部件与路由键的对应关系 """

    def __init__(self, stacked: QStackedWidget, routeKey: str):
        """
        初始化路由项
        
        参数:
            stacked (QStackedWidget): 关联的堆栈窗口部件
            routeKey (str): 路由键，对应子界面的对象名称(objectName)
        """
        self.stacked = stacked  # 堆栈窗口部件实例
        self.routeKey = routeKey  # 路由键（子界面唯一标识）

    def __eq__(self, other):
        """
        重写相等性比较方法，判断两个路由项是否相同
        
        参数:
            other: 待比较的另一个对象
            
        返回:
            bool: 若other是RouteItem实例且stacked和routeKey均相同则返回True，否则返回False
        """
        if other is None:  # 处理other为None的情况
            return False

        # 比较stacked实例和routeKey字符串是否完全一致
        return other.stacked is self.stacked and self.routeKey == other.routeKey


class StackedHistory:
    """ 堆栈历史记录 - 管理单个QStackedWidget的路由历史 """

    def __init__(self, stacked: QStackedWidget):
        """
        初始化堆栈历史记录
        
        参数:
            stacked (QStackedWidget): 关联的堆栈窗口部件
        """
        self.stacked = stacked  # 关联的堆栈窗口部件
        self.defaultRouteKey = None  # type: str  # 默认路由键（初始为None）
        self.history = [self.defaultRouteKey]   # type: List[str]  # 路由历史列表，初始包含默认路由键


    def __len__(self):
        """
        获取历史记录长度
        
        返回:
            int: 历史记录列表的长度
        """
        return len(self.history)

    def isEmpty(self):
        """
        判断历史记录是否为空（仅含默认路由键视为空）
        
        返回:
            bool: 若历史记录长度<=1则返回True，否则返回False
        """
        return len(self) <= 1

    def push(self, routeKey: str):
        """
        添加新路由键到历史记录
        
        参数:
            routeKey (str): 待添加的路由键
            
        返回:
            bool: 添加成功返回True，若与最后一项重复则返回False
        """
        # 避免添加重复路由键（与最后一项相同则不添加）
        if self.history[-1] == routeKey:
            return False

        self.history.append(routeKey)  # 添加新路由键到历史列表末尾
        return True

    def pop(self):
        """
        移除最后一条历史记录并跳转到新的顶部路由
        """
        if self.isEmpty():  # 历史记录为空时不操作
            return

        self.history.pop()  # 移除最后一项
        self.goToTop()  # 跳转到新的顶部路由

    def remove(self, routeKey: str):
        """
        从历史记录中移除指定路由键
        
        参数:
            routeKey (str): 待移除的路由键
        """
        if routeKey not in self.history:  # 路由键不存在时不操作
            return

        # 保留第一项（默认路由键），移除后续所有匹配的路由键
        self.history[1:] = [i for i in self.history[1:] if i != routeKey]
        # 去重连续重复项（使用groupby分组后取每组第一个元素）
        self.history = [k for k, g in groupby(self.history)]
        self.goToTop()  # 跳转到新的顶部路由

    def top(self):
        """
        获取当前顶部路由键
        
        返回:
            str: 历史记录列表的最后一项（当前路由键）
        """
        return self.history[-1]

    def setDefaultRouteKey(self, routeKey: str):
        """
        设置默认路由键
        
        参数:
            routeKey (str): 新的默认路由键
        """
        self.defaultRouteKey = routeKey  # 更新默认路由键
        self.history[0] = routeKey  # 更新历史列表第一项为默认路由键

    def goToTop(self):
        """
        跳转到当前顶部路由对应的界面
        """
        # 根据顶部路由键查找对应的QWidget（通过objectName匹配）
        w = self.stacked.findChild(QWidget, self.top())
        if w:  # 找到对应窗口部件时切换显示
            self.stacked.setCurrentWidget(w)


class Router(QObject):
    """ 路由管理器 - 管理多个堆栈窗口部件的路由历史，提供页面跳转和历史管理功能 """

    # 信号：历史记录为空状态变化时触发（参数为是否为空）
    emptyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        """
        初始化路由管理器
        
        参数:
            parent (QObject): 父对象（默认为None）
        """
        super().__init__(parent=parent)  # 调用父类QObject的初始化方法
        self.history = []   # 全局路由历史列表（存储RouteItem实例）
        self.stackHistories = {} # 堆栈历史字典（键:堆栈部件，值:StackedHistory实例）

    def setDefaultRouteKey(self, stacked: QStackedWidget, routeKey: str):
        """
        为指定堆栈窗口部件设置默认路由键
        
        参数:
            stacked (QStackedWidget): 目标堆栈窗口部件
            routeKey (str): 默认路由键（子界面的对象名称）
        """
        # 若堆栈部件不在字典中，则创建对应的StackedHistory实例
        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        # 设置该堆栈部件的默认路由键
        self.stackHistories[stacked].setDefaultRouteKey(routeKey)

    def push(self, stacked: QStackedWidget, routeKey: str):
        """
        添加路由到历史记录并切换界面
        
        参数:
            stacked (QStackedWidget): 目标堆栈窗口部件
            routeKey (str): 路由键（子界面的对象名称，用于标识子界面）
        """
        item = RouteItem(stacked, routeKey)  # 创建路由项实例

        # 若堆栈部件不在字典中，则创建对应的StackedHistory实例
        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        # 添加路由键到堆栈历史，避免重复添加
        success = self.stackHistories[stacked].push(routeKey)
        if success:  # 添加成功时，将路由项加入全局历史列表
            self.history.append(item)

        # 发送历史记录为空状态变化信号（历史列表为空则信号参数为True）
        self.emptyChanged.emit(not bool(self.history))

    def pop(self):
        """
        回退到上一条路由（移除最后一条历史记录）
        """
        if not self.history:  # 全局历史列表为空时不操作
            return

        item = self.history.pop()  # 移除最后一条全局历史记录
        # 发送历史记录为空状态变化信号
        self.emptyChanged.emit(not bool(self.history))
        # 回退对应堆栈部件的历史记录
        self.stackHistories[item.stacked].pop()

    def remove(self, routeKey: str):
        """
        从所有历史记录中移除指定路由键
        
        参数:
            routeKey (str): 待移除的路由键
        """
        # 过滤全局历史列表，保留路由键不匹配的项
        self.history = [i for i in self.history if i.routeKey != routeKey]
        # 去重连续重复的路由项（按routeKey分组后取每组第一个）
        self.history = [list(g)[0] for k, g in groupby(self.history, lambda i: i.routeKey)]
        # 发送历史记录为空状态变化信号
        self.emptyChanged.emit(not bool(self.history))

        # 遍历所有堆栈历史，移除包含该路由键的记录
        for stacked, history in self.stackHistories.items():
            # 查找该堆栈部件中是否存在对应路由键的窗口
            w = stacked.findChild(QWidget, routeKey)
            if w:  # 找到窗口时，从该堆栈历史中移除路由键
                return history.remove(routeKey)


# 路由管理器全局实例，供应用程序中其他模块调用
qrouter = Router()