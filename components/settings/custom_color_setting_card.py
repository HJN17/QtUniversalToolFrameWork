# coding:utf-8
from typing import Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QButtonGroup, QVBoxLayout, QPushButton, QHBoxLayout

from ..dialog_box import ColorDialog
# 从当前目录导入扩展设置卡片基类
from .expand_setting_card import ExpandGroupSettingCard
# 从widgets.button模块导入单选按钮组件
from ..widgets.button import RadioButton
# 从common.config导入配置管理对象和颜色配置项类
from common.config import qconfig, ColorConfigItem
# 从common.icon导入Fluent图标基类
from common.icon import FluentIconBase




class CustomColorSettingCard(ExpandGroupSettingCard):
    """ 自定义颜色设置卡片
    
    功能说明：
    - 提供"默认颜色"和"自定义颜色"两种选择
    - 支持通过颜色选择对话框设置自定义颜色
    - 与配置系统联动，自动保存和读取颜色设置
    """

    def __init__(self, configItem: ColorConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None, enableAlpha=False):
        """
        初始化自定义颜色设置卡片

        参数说明：
        ----------
        configItem: ColorConfigItem
            颜色配置项对象，用于读取默认值和保存用户设置
            
        icon: str | QIcon | FluentIconBase
            卡片左侧显示的图标，可以是路径字符串、QIcon对象或Fluent图标
            
        title: str
            卡片标题文本，显示在图标右侧
            
        content: str
            卡片内容描述文本，显示在标题下方（可选参数）
            
        parent: QWidget
            父窗口部件（可选参数）
            
        enableAlpha: bool
            是否启用透明度通道，True表示支持透明色选择，False仅支持RGB颜色
        """

        super().__init__(icon, title, content, parent=parent)
        # 保存透明度启用状态
        self.enableAlpha = enableAlpha
        # 保存颜色配置项对象
        self.configItem = configItem
        # 获取默认颜色（从配置项的默认值转换为QColor对象）
        self.defaultColor = QColor(configItem.defaultValue)
        # 获取当前自定义颜色（从配置中读取当前值并转换为QColor对象）
        self.customColor = QColor(qconfig.get(configItem))

        # 创建选择标签（显示当前选中的颜色模式：默认/自定义）
        self.choiceLabel = QLabel(self)

        # 创建单选按钮容器部件（放置在展开视图中）
        self.radioWidget = QWidget(self.view)
        # 创建单选按钮垂直布局
        self.radioLayout = QVBoxLayout(self.radioWidget)

        self.defaultRadioButton = RadioButton(
            '默认颜色', self.radioWidget)
        self.customRadioButton = RadioButton(
            '自定义颜色', self.radioWidget)
        # 创建按钮组，用于管理单选按钮的互斥选择
        self.buttonGroup = QButtonGroup(self)

        # 创建自定义颜色选择容器部件（放置在展开视图中）
        self.customColorWidget = QWidget(self.view)
        # 创建自定义颜色水平布局
        self.customColorLayout = QHBoxLayout(self.customColorWidget)
        # 创建"自定义颜色"标签
        self.customLabel = QLabel(
            '自定义颜色', self.customColorWidget)
        # 创建"选择颜色"按钮
        self.chooseColorButton = QPushButton(
            '选择颜色', self.customColorWidget)

        # 初始化界面控件
        self.__initWidget()

    def __initWidget(self):
        # 初始化界面布局
        self.__initLayout()

        # 根据默认颜色和当前自定义颜色是否一致，设置单选按钮状态
        if self.defaultColor != self.customColor:
            # 颜色不一致时，选中"自定义颜色"单选按钮，启用选择按钮
            self.customRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(True)
        else:
            # 颜色一致时，选中"默认颜色"单选按钮，禁用选择按钮
            self.defaultRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(False)

        # 设置选择标签文本为当前选中的单选按钮文本
        self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        # 根据文本内容调整标签大小
        self.choiceLabel.adjustSize()

        # 设置对象名称（用于样式表选择器）
        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.chooseColorButton.setObjectName('chooseColorButton')

        # 连接单选按钮组的点击信号到处理函数
        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        # 连接选择颜色按钮的点击信号到颜色对话框显示函数
        self.chooseColorButton.clicked.connect(self.__showColorDialog)

    def __initLayout(self):
        # 将选择标签添加到卡片主布局
        self.addWidget(self.choiceLabel)

        # 设置单选按钮布局间距为19像素
        self.radioLayout.setSpacing(19)
        # 设置布局内控件靠顶部对齐
        self.radioLayout.setAlignment(Qt.AlignTop)
        # 设置布局边距：左48px，上18px，右0px，下18px
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        # 将单选按钮添加到按钮组（实现互斥选择）
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        # 将单选按钮添加到布局
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        # 设置布局大小策略为最小尺寸（根据内容自动调整大小）
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        # 设置自定义颜色布局边距：左48px，上18px，右44px，下18px
        self.customColorLayout.setContentsMargins(48, 18, 44, 18)
        # 添加"自定义颜色"标签到布局，左对齐
        self.customColorLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        # 添加"选择颜色"按钮到布局，右对齐
        self.customColorLayout.addWidget(self.chooseColorButton, 0, Qt.AlignRight)
        # 设置布局大小策略为最小尺寸
        self.customColorLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        # 设置展开视图布局间距为0像素
        self.viewLayout.setSpacing(0)
        # 设置展开视图布局边距为0
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # 将单选按钮容器添加到展开组视图
        self.addGroupWidget(self.radioWidget)
        # 将自定义颜色容器添加到展开组视图
        self.addGroupWidget(self.customColorWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ 单选按钮点击事件处理函数 """
        # 如果点击的按钮与当前选中的按钮相同，则不处理
        if button.text() == self.choiceLabel.text():
            return

        # 更新选择标签文本为当前选中按钮的文本
        self.choiceLabel.setText(button.text())
        # 调整标签大小以适应新文本
        self.choiceLabel.adjustSize()

        # 根据选中的按钮类型更新状态
        if button is self.defaultRadioButton:
            # 选中"默认颜色"：禁用选择按钮，保存默认颜色到配置
            self.chooseColorButton.setDisabled(True)
            qconfig.set(self.configItem, self.defaultColor)
            # 如果默认颜色与自定义颜色不同，发射颜色变更信号
            if self.defaultColor != self.customColor:
                self.__onColorChanged(self.customColor)
        else:
            # 选中"自定义颜色"：启用选择按钮，保存当前自定义颜色到配置
            self.chooseColorButton.setDisabled(False)
            qconfig.set(self.configItem, self.customColor)
            # 如果默认颜色与自定义颜色不同，发射颜色变更信号
            if self.defaultColor != self.customColor:
                self.__onColorChanged(self.customColor)

    def __showColorDialog(self):
        """ 显示颜色选择对话框 """
        # 创建颜色对话框：初始颜色为配置中的当前值，标题为"Choose color"，父窗口为当前窗口，启用透明度控制
        w = ColorDialog(
            qconfig.get(self.configItem), '选择颜色', self.window())
        # 连接颜色变更信号到自定义颜色变更处理函数
        w.colorChanged.connect(self.__onColorChanged)
        # 以模态方式显示对话框
        w.exec() # 阻塞式显示对话框，返回值为对话框的执行状态

    def __onColorChanged(self, color):
        """ 颜色变更处理函数 """
        # 将新颜色保存到配置
        qconfig.set(self.configItem, color,save=True)
        # # 更新自定义颜色变量
        # self.customColor = QColor(color)
        # # 发射颜色变更信号
        # self.colorChanged.emit(color)
