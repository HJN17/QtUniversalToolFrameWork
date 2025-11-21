# coding:utf-8
from enum import Enum
from string import Template
from typing import List, Union
import weakref  # 导入weakref模块，用于创建弱引用，避免因强引用导致的内存泄漏（如管理组件生命周期）
from PyQt5.QtCore import QFile, QObject, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget,QGraphicsDropShadowEffect
from .config import qconfig, Theme, isDarkTheme





class StyleSheetManager(QObject):
    """ 样式表管理器，用于注册、管理和自动更新界面组件的样式表 """

    def __init__(self):
        super().__init__()
        self.widgets = weakref.WeakKeyDictionary()  # 弱引用字典，存储组件与样式表的映射

    def register(self, source, widget: QWidget, reset=True):
        """ 向管理器注册组件，使其样式表可被自动管理
        
        参数
        ----------
        source: str | StyleSheetBase
            样式源，可以是：
            * `str`: QSS文件路径（会自动转换为StyleSheetFile实例）
            * `StyleSheetBase`: 自定义样式表示例（如FluentStyleSheet）
        
        widget: QWidget
            需要应用样式表的界面组件
        
        reset: bool
            是否重置样式源：
            - True：覆盖现有样式源
            - False：在现有样式源基础上追加
        """
        
        if isinstance(source, str):
            source = StyleSheetFile(source) # 若为字符串，转换为StyleSheetFile实例（文件型样式源）
        
        if widget not in self.widgets: # 若组件未注册
            widget.destroyed.connect(lambda: self.deregister(widget)) # 绑定组件销毁信号：组件销毁时自动从管理器注销
            widget.installEventFilter(DirtyStyleSheetWatcher(widget)) # 为组件安装脏样式表监听器：标记样式表需要延迟更新（优化性能）
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)]) # 初始化组件的样式源组合：基础样式源 + 组件自定义样式源

        if not reset:
            self.source(widget).add(source)
        else:
            # 重置：覆盖为新的样式源组合
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

    def deregister(self, widget: QWidget):   
        if widget not in self.widgets:
            return

        self.widgets.pop(widget)

    def items(self):
        return self.widgets.items()

    def source(self, widget: QWidget):
        """ 获取组件当前的样式源组合
        
        参数
        ----------
        widget: QWidget
            目标界面组件
        
        返回
        ----------
        StyleSheetCompose: 组件的样式源组合对象（包含一个或多个样式源）
        """
        return self.widgets.get(widget, StyleSheetCompose([]))

styleSheetManager = StyleSheetManager() # 创建全局样式表管理器实例，供外部模块注册和管理组件样式表


class StyleSheetBase:
    """ 样式表基类，定义样式源的通用接口（文件型、自定义型样式源均继承此类） """

    def path(self, theme=Theme.AUTO):
        raise NotImplementedError

    def content(self, theme=Theme.AUTO):
        return getStyleSheetFromFile(self.path(theme))

    def apply(self, widget: QWidget, theme=Theme.AUTO):
        setStyleSheet(widget, self, theme)

class StyleSheetCompose(StyleSheetBase):
    """ 样式表组合类，继承自StyleSheetBase，用于组合多个样式源（如基础样式+自定义样式） """

    def __init__(self, sources: List[StyleSheetBase]):
        self.sources = sources

    def content(self, theme=Theme.AUTO):
    
        return '\n'.join([i.content(theme) for i in self.sources])

    def add(self, source: StyleSheetBase):
        """ 向组合中添加新的样式源"""

        if source is self or source in self.sources:
            return

        self.sources.append(source)

    def remove(self, source: StyleSheetBase):
        """ 从组合中移除指定的样式源 """
       
        if source not in self.sources:
            return

        self.sources.remove(source)

class FluentStyleSheet(StyleSheetBase, Enum):
    """ Fluent风格内置样式表枚举，定义各组件的预设样式（如按钮、对话框等） """

    MENU = "menu"   # 菜单组件样式
    LABEL = "label" # 标签组件样式
    PIVOT = "pivot" # 选项卡组件样式
    BUTTON = "button" # 按钮组件样式
    DIALOG = "dialog" # 对话框组件样式
    SLIDER = "slider" # 滑块组件样式
    INFO_BAR = "info_bar" # 信息提示条组件样式
    SPIN_BOX = "spin_box" # 数字输入框组件样式
    TAB_VIEW = "tab_view" # 标签页组件样式
    TOOL_TIP = "tool_tip" # 工具提示组件样式    
    CHECK_BOX = "check_box" # 复选框组件样式
    COMBO_BOX = "combo_box" # 下拉框组件样式
    FLIP_VIEW = "flip_view" # 翻转视图组件样式  
    LINE_EDIT = "line_edit" # 单行输入框组件样式
    LIST_VIEW = "list_view" # 列表视图组件样式
    TREE_VIEW = "tree_view" # 树视图组件样式
    INFO_BADGE = "info_badge" # 信息标记组件样式
    PIPS_PAGER = "pips_pager" # 页码导航组件样式
    TABLE_VIEW = "table_view" # 表格视图组件样式
    CARD_WIDGET = "card_widget" # 卡片组件样式
    TIME_PICKER = "time_picker" # 时间选择器组件样式
    COLOR_DIALOG = "color_dialog"   # 颜色选择对话框组件样式
    MEDIA_PLAYER = "media_player"   # 媒体播放器组件样式
    SETTING_CARD = "setting_card"   # 设置卡片组件样式
    TEACHING_TIP = "teaching_tip"   # 教学提示组件样式
    FLUENT_WINDOW = "fluent_window" # fluent风格窗口组件样式
    SWITCH_BUTTON = "switch_button" # 开关按钮组件样式
    MESSAGE_DIALOG = "message_dialog"   # 消息对话框组件样式
    STATE_TOOL_TIP = "state_tool_tip"   # 状态工具提示组件样式
    CALENDAR_PICKER = "calendar_picker" # 日历选择器组件样式
    FOLDER_LIST_DIALOG = "folder_list_dialog"   # 文件夹列表对话框组件样式
    SETTING_CARD_GROUP = "setting_card_group"   # 设置卡片组组件样式
    EXPAND_SETTING_CARD = "expand_setting_card"   # 可展开设置卡片组件样式
    NAVIGATION_INTERFACE = "navigation_interface"   # 导航界面组件样式

    def path(self, theme=Theme.AUTO):
        
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme
        
        return f":/resource/qss/{theme.value.lower()}/{self.value}.qss"

class StyleSheetFile(StyleSheetBase):
    """ 文件型样式源类，继承自StyleSheetBase，用于从本地文件加载样式表 """

    def __init__(self, path: str):
        super().__init__()
        self.filePath = path

    def path(self, theme=Theme.AUTO):
        
        return self.filePath

class CustomStyleSheet(StyleSheetBase):
    """ 自定义样式源类，继承自StyleSheetBase，用于存储组件的自定义样式（支持浅色/深色主题区分） """

    DARK_QSS_KEY = 'darkCustomQss'  # 深色主题自定义QSS的动态属性名（用于组件存储深色样式）
    LIGHT_QSS_KEY = 'lightCustomQss'    # 浅色主题自定义QSS的动态属性名（用于组件存储浅色样式）
    
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self._widget = weakref.ref(widget) # 把 widget 对象的弱引用保存到 self._widget

    def path(self, theme=Theme.AUTO):
        return ''

    @property
    def widget(self):
        """ 获取弱引用指向的组件（可能为None，若组件已销毁） """
        return self._widget()

    def __eq__(self, other: object) -> bool:

        """ 重写相等性判断：两个CustomStyleSheet实例相等当且仅当它们指向同一个组件 """

        if not isinstance(other, CustomStyleSheet): 
            return False # 若比较对象不是CustomStyleSheet实例，直接返回False

        return other.widget is self.widget  # 比较两个实例的组件弱引用是否指向同一个组件

    def setCustomStyleSheet(self, lightQss: str, darkQss: str):
        """ 为组件设置自定义样式表（同时指定浅色和深色主题）"""
        if self.widget:
            self.widget.setProperty(self.LIGHT_QSS_KEY, lightQss)
            self.widget.setProperty(self.DARK_QSS_KEY, darkQss)
        return self

    def content(self, theme=Theme.AUTO) -> str:
        """ 获取当前主题对应的自定义样式表内容（重写StyleSheetBase.content方法）"""
        
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme

        if not self.widget:
            return ''

        if theme == Theme.LIGHT:
            return self.widget.property(self.LIGHT_QSS_KEY) or ''
        return self.widget.property(self.DARK_QSS_KEY) or ''

class DirtyStyleSheetWatcher(QObject):
    """ 脏样式表监听器，继承自QObject，用于延迟更新组件样式表（优化主题切换性能） """

    def eventFilter(self, obj: QWidget, e: QEvent):
        """ 事件过滤器：监听组件的绘制事件，延迟更新脏样式表
        
        参数
        ----------
        obj: QWidget
            被监听的组件
        e: QEvent
            事件对象
        
        返回
        ----------
        bool: 事件是否被过滤（此处始终返回False，不阻止事件传播）
        """
        # 判断事件类型是否为绘制事件，且组件是否标记了"脏样式表"
        if e.type() != QEvent.Type.Paint or not obj.property('dirty-qss'):
            return super().eventFilter(obj, e)
        
        # 清除"脏样式表"标记
        obj.setProperty('dirty-qss', False)
     
        if obj in styleSheetManager.widgets:
            obj.setStyleSheet(getStyleSheet(styleSheetManager.source(obj)))

        return super().eventFilter(obj, e)

class QssTemplate(Template):
    """ QSS样式表模板类，继承自string.Template，用于QSS变量替换 """
    delimiter = '--'

def applyThemeColor(qss: str):
    """ 将主题色变量替换为实际颜色值，应用到QSS样式表中
    
    参数
    ----------
    qss: str
        待处理的QSS字符串，其中需要替换的变量名需与ThemeColor枚举值一致，
        且以'--'为前缀（如'--ThemeColorPrimary'对应主题主色）
    
    返回
    ----------
    str: 替换后的QSS字符串（包含实际颜色值）
    """
    template = QssTemplate(qss)
    # 构建变量映射：键为ThemeColor枚举值（如'ThemeColorPrimary'），值为实际颜色值（如'#0078D7'）
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    # 安全替换模板变量（仅替换存在的键，避免KeyError）
    return template.safe_substitute(mappings)

def getStyleSheetFromFile(file: Union[str, QFile]):
    """ 从文件读取QSS样式表内容（支持路径字符串或QFile对象）"""
    f = QFile(file)
    f.open(QFile.ReadOnly)
    qss = str(f.readAll(), encoding='utf-8')
    f.close()
    return qss

def getStyleSheet(source: Union[str, StyleSheetBase], theme=Theme.AUTO):
    """ 获取组件当前的样式表内容（根据主题模式应用主题色替换）"""
    if isinstance(source, str):
        source = StyleSheetFile(source)

    return applyThemeColor(source.content(theme))

def setStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):

    if register:
        styleSheetManager.register(source, widget)

    widget.setStyleSheet(getStyleSheet(source, theme))

def setCustomStyleSheet(widget: QWidget, lightQss: str, darkQss: str):
    """ 为组件设置自定义样式表（分别指定浅色和深色主题）"""
    CustomStyleSheet(widget).setCustomStyleSheet(lightQss, darkQss)
    updateStyleSheet(True)
    

def updateStyleSheet(lazy=False):
    """ 更新所有已注册组件的样式表（通常在主题切换时调用）
    
    参数
    ----------
    lazy: bool
        是否延迟更新（True则仅更新可见组件，不可见组件标记为"脏样式表"，下次绘制时更新，优化性能）
    """
    
    removes = []

    for widget, file in styleSheetManager.items():
        try:
            # 判断是否延迟更新且组件不可见（可见区域为空）
            if not (lazy and widget.visibleRegion().isNull()):
                # 非延迟更新或组件可见：直接更新样式表
                setStyleSheet(widget, file, qconfig.themeMode.value)
            else:
                # 延迟更新且组件不可见：重新注册样式源并标记"脏样式表"
                styleSheetManager.register(file, widget)
                widget.setProperty('dirty-qss', True)
        except RuntimeError:
            removes.append(widget)
            
    for widget in removes:
        styleSheetManager.deregister(widget)



class ThemeColor(Enum):
    """ 主题颜色枚举，定义不同深浅的主题色系（基于主题主色派生） """
    PRIMARY = "ThemeColorPrimary"   # 主题主色（原始主题色）
    DARK_1 = "ThemeColorDark1"   # 主题深色1（比主色暗10%）
    DARK_2 = "ThemeColorDark2"   # 主题深色2（比主色暗18%）
    DARK_3 = "ThemeColorDark3"   # 主题深色3（比主色暗30%）
    LIGHT_1 = "ThemeColorLight1"   # 主题浅色1（比主色亮5%）    
    LIGHT_2 = "ThemeColorLight2"    # 主题浅色2（比主色亮15%，饱和度降低22%）
    LIGHT_3 = "ThemeColorLight3"   # 主题浅色3（比主色亮25%，饱和度降低35%）

    def name(self):
        """ 获取当前主题色的十六进制颜色字符串（如'#0078D7'）
        
        返回
        ----------
        str: 十六进制颜色字符串（带'#'前缀）
        """
        return self.color().name()

    def color(self):
        """ 获取当前主题色的QColor对象（根据当前主题动态调整HSV值）
        
        返回
        ----------
        QColor: 调整后的主题色对象
        """
        # 获取全局配置的主题主色（QColor对象）
        color = qconfig.get(qconfig.themeColor)  # type:QColor

        # 将颜色转换为HSV色彩空间（H:色相, S:饱和度, V:明度, A:透明度）
        h, s, v, _ = color.getHsvF()

        # 根据当前主题调整HSV值（深色主题和浅色主题调整策略不同）
        if isDarkTheme():
            # 深色主题：降低饱和度，固定明度为1（最亮）
            s *= 0.84
            v = 1
            # 根据当前颜色类型进一步调整
            if self == self.DARK_1:
                v *= 0.9  # 明度降低10%
            elif self == self.DARK_2:
                s *= 0.977  # 饱和度降低2.3%
                v *= 0.82   # 明度降低18%
            elif self == self.DARK_3:
                s *= 0.95   # 饱和度降低5%
                v *= 0.7    # 明度降低30%
            elif self == self.LIGHT_1:
                s *= 0.92   # 饱和度降低8%
            elif self == self.LIGHT_2:
                s *= 0.78   # 饱和度降低22%
            elif self == self.LIGHT_3:
                s *= 0.65   # 饱和度降低35%
        else:
            # 浅色主题：根据颜色类型调整明度和饱和度
            if self == self.DARK_1:
                v *= 0.75   # 明度降低25%
            elif self == self.DARK_2:
                s *= 1.05   # 饱和度提高5%
                v *= 0.5    # 明度降低50%
            elif self == self.DARK_3:
                s *= 1.1    # 饱和度提高10%
                v *= 0.4    # 明度降低60%
            elif self == self.LIGHT_1:
                v *= 1.05   # 明度提高5%
            elif self == self.LIGHT_2:
                s *= 0.75   # 饱和度降低25%
                v *= 1.05   # 明度提高5%
            elif self == self.LIGHT_3:
                s *= 0.65   # 饱和度降低35%
                v *= 1.05   # 明度提高5%

        # 根据调整后的HSV值创建并返回QColor对象（确保S和V不超过1.0）
        return QColor.fromHsvF(h, min(s, 1), min(v, 1))


def themeColor():
    """ 获取当前主题的主色（ThemeColor.PRIMARY）
    
    返回
    ----------
    QColor: 主题主色对象
    """
    return ThemeColor.PRIMARY.color()


def setTheme(lazy=False):
    """ 设置应用程序主题（全局生效）"""

    updateStyleSheet(lazy)

def updateThemeColor(lazy=False):
   
    updateStyleSheet(lazy)


def setShadowEffect(view, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        """ 为对话框添加阴影效果
        blurRadius: 模糊半径
        offset: 阴影偏移量
        color: 阴影颜色
        """
        # 创建阴影效果对象
        shadowEffect = QGraphicsDropShadowEffect(view)
        # 设置模糊半径
        shadowEffect.setBlurRadius(blurRadius)
        # 设置阴影偏移
        shadowEffect.setOffset(*offset)
        # 设置阴影颜色
        shadowEffect.setColor(color)
        # 清除之前的阴影效果
        view.setGraphicsEffect(None)
        # 设置新的阴影效果
        view.setGraphicsEffect(shadowEffect)




class StyleSheet(StyleSheetBase, Enum):
    """ 样式表枚举类，定义了应用程序中使用的所有样式表文件 """
    
    GALLERY_INTERFACE = "gallery_interface"
    SAMPLE_CARD = "sample_card"
    HOME_INTERFACE = "home_interface"
    SETTING_INTERFACE = "setting_interface"
    
    def path(self, theme=Theme.AUTO):
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme
        return f":/resource/qss/{theme.value.lower()}/{self.value}.qss"

