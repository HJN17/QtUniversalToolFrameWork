# coding:utf-8
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

from ...common.style_sheet import FluentStyleSheet
from ...common.font import setFont

from ..layout.expand_layout import ExpandLayout


class SettingCardGroup(QWidget):

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()

    def addSettingCard(self, card: QWidget):
        """ 
        向设置卡片组添加单个设置卡片
        
        参数:
            card (QWidget): 要添加的设置卡片控件（如SwitchSettingCard、OptionsSettingCard等）
        """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    # 添加多个设置卡片到组：批量添加卡片，内部调用addSettingCard逐个处理
    def addSettingCards(self, cards: List[QWidget]):
        """ 
        向设置卡片组批量添加多个设置卡片
        
        参数:
            cards (List[QWidget]): 要添加的设置卡片控件列表（元素类型同addSettingCard的card参数）
        """
        # 遍历卡片列表：逐个调用addSettingCard添加卡片
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self):
        # 计算总高度：卡片布局高度（通过heightForWidth获取） + 标题区域高度（固定46px，含标题高度和间距）
        h = self.cardLayout.heightForWidth(self.width()) + 46
        return self.resize(self.width(), h)
