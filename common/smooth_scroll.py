# coding:utf-8
# 导入必要的模块：deque用于双端队列操作，Enum用于枚举类型，数学函数用于平滑算法
from collections import deque  # 双端队列，用于存储滚动时间戳和待处理步骤
from enum import Enum  # 枚举基类，用于定义平滑滚动模式
from math import cos, pi  # 数学函数，用于余弦插值计算

# 导入PyQt相关模块：用于GUI事件处理和组件交互
from PyQt5.QtCore import QDateTime, Qt, QTimer, QPoint  # Qt核心模块：日期时间、定时器、坐标点等
from PyQt5.QtGui import QWheelEvent  # Qt GUI模块：滚轮事件类
from PyQt5.QtWidgets import QApplication, QScrollArea, QAbstractScrollArea  # Qt组件模块：应用程序、滚动区域组件


class SmoothScroll:
    """ 
    平滑滚动功能实现类
    
    为QScrollArea组件提供平滑滚动效果，支持多种滚动插值模式，
    可根据滚动频率动态调整加速度，提升用户滚动体验。
    """

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical):
        """
        初始化平滑滚动实例
        
        参数
        ----------
        widget: QScrollArea
            需要应用平滑滚动效果的滚动区域组件
        
        orient: Qt.Orientation
            滚动方向（默认垂直方向Qt.Vertical，可选水平方向Qt.Horizontal）
        """
        self.widget = widget  # 目标滚动区域组件
        self.orient = orient  # 滚动方向
        self.fps = 60  # 平滑滚动帧率（每秒60帧）
        self.duration = 400  # 单次滚动动画持续时间（毫秒）
        self.stepsTotal = 0  # 单次滚动总步数（=帧率*持续时间/1000）
        self.stepRatio = 1.5  # 步长放大比例（增强滚动距离）
        self.acceleration = 1  # 加速度系数（基础加速度）
        self.lastWheelEvent = None  # 最后一次滚轮事件（用于构造模拟事件）
        self.scrollStamps = deque()  # 滚动事件时间戳队列（记录最近500ms内的滚动事件）
        self.stepsLeftQueue = deque()  # 待处理滚动步骤队列（存储[总距离, 剩余步数]）
        self.smoothMoveTimer = QTimer(widget)  # 平滑滚动定时器（控制每帧滚动距离）
        self.smoothMode = SmoothMode(SmoothMode.LINEAR)  # 默认平滑模式（线性插值）
        self.smoothMoveTimer.timeout.connect(self.__smoothMove)  # 绑定定时器超时回调

    def setSmoothMode(self, smoothMode):
        """ 
        设置平滑滚动模式
        
        参数
        ----------
        smoothMode: SmoothMode
            平滑模式枚举值（如线性、余弦等）
        """
        self.smoothMode = smoothMode

    def wheelEvent(self, e):
        # 仅处理鼠标触发的滚轮事件（忽略触摸板等其他设备，修复#75问题）
        # delta：滚轮事件的滚动距离（垂直方向优先，水平方向次之）
        delta = e.angleDelta().y() if e.angleDelta().y() != 0 else e.angleDelta().x()
        
        # 若禁用平滑或滚动距离非标准值（120的倍数），直接使用原生滚动
        if self.smoothMode == SmoothMode.NO_SMOOTH or abs(delta) % 120 != 0:
            QAbstractScrollArea.wheelEvent(self.widget, e)
            return

        # 记录当前滚动事件时间戳（用于计算加速度）
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()  # 当前时间戳（毫秒）
        self.scrollStamps.append(now)  # 将当前时间戳加入队列
        # 移除500ms前的旧时间戳（只保留最近500ms内的滚动事件）
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        # 根据未处理事件数量调整加速度比例（最多15个事件，比例上限1.0）
        accerationRatio = min(len(self.scrollStamps) / 15, 1)
        
        # 记录最后一次滚轮事件（用于构造模拟事件）
        if not self.lastWheelEvent:
            self.lastWheelEvent = QWheelEvent(e)  # 初始化最后事件
        else:
            self.lastWheelEvent = e  # 更新最后事件

        # 计算总步数（帧率*持续时间/1000，如60帧*400ms=24步）
        self.stepsTotal = self.fps * self.duration / 1000

        # 计算单步滚动距离（基础距离*步长比例+加速度补偿）
        delta = delta * self.stepRatio  # 基础距离放大
        if self.acceleration > 0:
            delta += delta * self.acceleration * accerationRatio  # 叠加加速度

        # 将[总距离, 剩余步数]加入待处理队列（用于分步滚动）
        self.stepsLeftQueue.append([delta, self.stepsTotal])

        # 启动定时器（按帧率间隔触发平滑滚动，如60帧=16ms/步）
        self.smoothMoveTimer.start(int(1000 / self.fps))

    def __smoothMove(self):
        """ 定时器超时回调：处理平滑滚动的每一步 """
        totalDelta = 0  # 本轮滚动总距离（累加所有待处理事件的单步距离）

        # 遍历待处理队列，计算每步滚动距离并减少剩余步数
        for i in self.stepsLeftQueue:
            # i[0]：总滚动距离；i[1]：剩余步数
            totalDelta += self.__subDelta(i[0], i[1])  # 累加单步插值距离
            i[1] -= 1  # 剩余步数减1

        # 移除已处理完毕的事件（剩余步数为0）
        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        # 根据滚动方向构造滚动距离点和目标滚动条
        if self.orient == Qt.Vertical:
            p = QPoint(0, round(totalDelta))  # 垂直滚动：y分量为滚动距离
            bar = self.widget.verticalScrollBar()  # 垂直滚动条
        else:
            p = QPoint(round(totalDelta), 0)  # 水平滚动：x分量为滚动距离
            bar = self.widget.horizontalScrollBar()  # 水平滚动条

        # 构造模拟滚轮事件（使用最后一次滚轮事件的参数，仅修改滚动距离）
        e = QWheelEvent(
            self.lastWheelEvent.pos(),  # 事件位置
            self.lastWheelEvent.globalPos(),  # 全局位置
            QPoint(),  # 像素滚动距离（未使用）
            p,  # 角度滚动距离（实际滚动距离）
            round(totalDelta),  # 总滚动距离
            self.orient,  # 滚动方向
            self.lastWheelEvent.buttons(),  # 鼠标按键状态
            Qt.NoModifier  # 键盘修饰键状态
        )

        # 向滚动条发送模拟滚轮事件（实现平滑滚动效果）
        QApplication.sendEvent(bar, e)

        # 若队列空则停止定时器（无待处理事件时结束滚动）
        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def __subDelta(self, delta, stepsLeft):
        """ 
        计算单步滚动距离（根据平滑模式进行插值）
        
        参数
        ----------
        delta: float
            总滚动距离
        
        stepsLeft: int
            剩余步数
        
        返回
        ----------
        float: 单步滚动距离（插值结果）
        """
        m = self.stepsTotal / 2  # 中点步数（总步数的一半）
        x = abs(self.stepsTotal - stepsLeft - m)  # 当前步到中点的距离（绝对值）

        res = 0  # 单步滚动距离结果
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0  # 无平滑：不滚动
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal  # 恒定速度：总距离/总步数
        elif self.smoothMode == SmoothMode.LINEAR:
            # 线性插值：速度与到中点距离成正比（先加速后减速）
            res = 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATI:
            # 二次插值：速度按二次曲线变化（更快加速，更慢减速）
            res = 3 / 4 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            # 余弦插值：速度按余弦曲线变化（平滑无突变）
            res = (cos(x * pi / m) + 1) / (2 * m) * delta

        return res


class SmoothMode(Enum):
    """ 
    平滑滚动模式枚举
    
    定义不同的滚动速度曲线算法，影响滚动的平滑度和手感
    """
    NO_SMOOTH = 0  # 无平滑滚动（使用原生滚动）
    CONSTANT = 1   # 恒定速度（匀速滚动）
    LINEAR = 2     # 线性插值（速度先增后减，线性变化）
    QUADRATI = 3   # 二次插值（速度按二次曲线变化，更柔和）
    COSINE = 4     # 余弦插值（速度按余弦曲线变化，最平滑）
