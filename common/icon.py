# coding:utf-8
from enum import Enum 
from typing import Union 
import json 

from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import QRectF, Qt, QFile, QObject, QRect
from PyQt5.QtGui import (QIcon, QIconEngine, QColor, QPixmap, QImage, QPainter,QFontDatabase, QFont, QPainterPath)
from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtSvg import QSvgRenderer

from .config import isDarkTheme, Theme
from .overload import singledispatchmethod


class FluentIconEngine(QIconEngine):
    """ 自定义Fluent风格图标引擎"""

    def __init__(self, icon):
        
        super().__init__() 
        self.icon = icon

    def paint(self, painter, rect, mode, state):
        painter.save() # 保存当前绘图状态（避免影响后续绘制）

        if mode == QIcon.Disabled:
            painter.setOpacity(0.5)
        elif mode == QIcon.Selected: 
            painter.setOpacity(0.7)

        theme = Theme.AUTO
        
        icon = self.icon
        if isinstance(self.icon, Icon):
            icon = self.icon.fluentIcon.icon(theme)
        elif isinstance(self.icon, FluentIconBase): 
            icon = self.icon.icon(theme) 

        if rect.x() == 19:
            rect = rect.adjusted(-1, 0, 0, 0)  # 调整矩形：左移1px，其他方向不变

        icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, state)
        painter.restore()

    def clone(self) -> QIconEngine:
        return FluentIconEngine(self.icon, self.isThemeReversed) 

    def pixmap(self, size, mode, state):
        
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        self.paint(painter, rect, mode, state)
        return pixmap 

class SvgIconEngine(QIconEngine):
    """ SVG图标引擎（用于渲染SVG格式图标） """

    def __init__(self, svg: str):
        super().__init__()
        self.svg = svg

    def paint(self, painter, rect, mode, state):
        drawSvgIcon(self.svg.encode(), painter, rect)  # 编码为bytes后绘制

    def clone(self) -> QIconEngine:
        """ 创建引擎副本 """
        return SvgIconEngine(self.svg)

    def pixmap(self, size, mode, state):
        """ 生成SVG图标像素图（逻辑与FluentIconEngine类似） """
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        self.paint(painter, rect, mode, state)
        return pixmap

class FontIconEngine(QIconEngine):
    """ 字体图标引擎（用于渲染字体文件中的图标，如IconFont） """

    def __init__(self, fontFamily: str, char: str, color, isBold):
       
        super().__init__()
        self.color = color  
        self.char = char 
        self.fontFamily = fontFamily  
        self.isBold = isBold 

    def paint(self, painter, rect, mode, state):
        """ 绘制字体图标 """
     
        font = QFont(self.fontFamily) 
        font.setBold(self.isBold)
        font.setPixelSize(round(rect.height()))  # 字体大小=图标高度（取整）

        painter.setFont(font)  # 设置字体
        painter.setPen(Qt.PenStyle.NoPen)  # 禁用画笔（避免轮廓线）
        painter.setBrush(self.color)  # 设置画刷颜色（填充图标）
        # 启用抗锯齿和文本抗锯齿（使图标边缘平滑）
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        # 创建绘制路径并添加文本
        path = QPainterPath()
        # 添加文本：位置（rect左上角），字体，字符
        path.addText(rect.x(), rect.y() + rect.height(), font, self.char)
        painter.drawPath(path)  # 绘制路径（即图标）

    def clone(self) -> QIconEngine:
        """ 创建引擎副本 """
        return FontIconEngine(self.fontFamily, self.char, self.color, self.isBold)

    def pixmap(self, size, mode, state):
        """ 生成字体图标像素图（逻辑与其他引擎类似） """
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        self.paint(painter, rect, mode, state)
        return pixmap


def getIconColor(theme=Theme.AUTO, reverse=False):
    """
    根据主题获取图标颜色
    
    Parameters
    ----------
    theme: Theme
        目标主题（AUTO/LIGHT/DARK）
    
    reverse: bool
        是否反转颜色（True时交换浅色/深色颜色）
    
    Returns
    -------
    str
        图标颜色字符串（"black"或"white"）
    """
    
    if not reverse:
        lc, dc = "black", "white"  # 不反转：浅色→黑，深色→白
    else:
        lc, dc = "white", "black"  # 反转：浅色→白，深色→黑

    if theme == Theme.AUTO:
        color = dc if isDarkTheme() else lc  # AUTO：跟随系统主题
    else:
        color = dc if theme == Theme.DARK else lc  # 指定主题：深色→dc，浅色→lc

    return color


def drawSvgIcon(icon, painter, rect):
    
    renderer = QSvgRenderer(icon) 
    renderer.render(painter, QRectF(rect))  # 渲染SVG到指定区域


def writeSvg(iconPath: str, indexes=None, **attributes):
    """
    修改SVG图标属性并返回修改后的SVG代码
    
    Parameters
    ----------
    iconPath: str
        SVG文件路径
    
    indexes: List[int]
        需要修改属性的path元素索引列表（None则修改所有path）
    
    **attributes:
        要设置的SVG属性（如fill="#FF0000"设置填充色）
    
    Returns
    -------
    str
        修改后的SVG代码
    """
    if not iconPath.lower().endswith('.svg'):  # 检查是否为SVG文件
        return ""  # 非SVG文件返回空字符串

    # 读取SVG文件内容
    f = QFile(iconPath)
    f.open(QFile.ReadOnly)  # 只读模式打开
    dom = QDomDocument()  # 创建XML文档对象
    dom.setContent(f.readAll())  # 加载SVG内容到文档
    f.close()  # 关闭文件

    # 修改指定path元素的属性
    pathNodes = dom.elementsByTagName('path')  # 获取所有path元素
    # 确定要修改的path索引（默认所有）
    indexes = range(pathNodes.length()) if not indexes else indexes
    for i in indexes:
        element = pathNodes.at(i).toElement()  # 获取第i个path元素
        for k, v in attributes.items():  # 设置属性（如fill、stroke等）
            element.setAttribute(k, v)

    return dom.toString()  # 返回修改后的SVG代码字符串


def drawIcon(icon, painter, rect, state=QIcon.Off, **attributes):
    """
    统一绘制图标（支持多种图标类型）
    
    Parameters
    ----------
    icon: str | QIcon | FluentIconBase
        图标路径、QIcon对象或FluentIconBase子类
    
    painter: QPainter
        绘图工具对象
    
    rect: QRect | QRectF
        绘制区域
    
    state: QIcon.State
        图标状态（On/Off）
    
    **attributes:
        SVG图标额外属性（如fill、stroke）
    """
    if isinstance(icon, FluentIconBase):  # Fluent图标基类：调用其render方法
        icon.render(painter, rect, **attributes)
    elif isinstance(icon, Icon):  # Icon包装类：调用内部FluentIcon的render
        icon.fluentIcon.render(painter, rect, **attributes)
    else:  # 其他类型（如QIcon或路径）：转换为QIcon绘制
        icon = QIcon(icon)
        icon.paint(painter, QRectF(rect).toRect(), Qt.AlignCenter, state=state)


class FluentIconBase:
    """ Fluent图标基类（定义Fluent风格图标的基本接口） """
    
    def path(self, theme=Theme.AUTO) -> str:
        raise NotImplementedError

    def icon(self, theme=Theme.AUTO, color: QColor = None) -> QIcon:
        """
        创建QIcon对象（支持主题和自定义颜色）
        
        Parameters
        ----------
        theme: Theme
            图标主题
        
        color: QColor
            自定义图标颜色（仅对SVG图标有效）
        
        Returns
        -------
        QIcon
            创建的图标对象
        """
        path = self.path(theme)  # 获取图标路径

        # 如果不是SVG文件或未指定颜色，直接返回QIcon
        if not (path.endswith('.svg') and color):
            return QIcon(self.path(theme))

        # 否则，修改SVG颜色并返回自定义图标
        color = QColor(color).name()  # 转换颜色为十六进制字符串（如"#FF0000"）
        return QIcon(SvgIconEngine(writeSvg(path, fill=color)))  # 使用SvgIconEngine渲染

    def colored(self, lightColor: QColor, darkColor: QColor) -> "ColoredFluentIcon":
        """
        创建支持自定义颜色的图标（浅色/深色主题分别设置颜色）
        
        Parameters
        ----------
        lightColor: QColor
            浅色主题下的图标颜色
        
        darkColor: QColor
            深色主题下的图标颜色
        
        Returns
        -------
        ColoredFluentIcon
            带自定义颜色的图标对象
        """
        return ColoredFluentIcon(self, lightColor, darkColor)

    def qicon(self) -> QIcon:
        return QIcon(FluentIconEngine(self))

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        """
        直接渲染图标到指定区域
        
        Parameters
        ----------
        painter: QPainter
            绘图工具
        
        rect: QRect | QRectF
            绘制区域
        
        theme: Theme
            图标主题
        
        indexes: List[int]
            需要修改属性的SVG path索引
        
        **attributes:
            SVG属性（如fill、stroke）
        """
        icon = self.path(theme)  # 获取图标路径

        if icon.endswith('.svg'):  # SVG图标：支持修改属性
            if attributes:  # 如果有属性需要修改
                icon = writeSvg(icon, indexes, **attributes).encode()
            drawSvgIcon(icon, painter, rect)  # 绘制SVG图标
        else:  # 非SVG图标（如位图）：使用QIcon绘制
            icon = QIcon(icon)
            rect = QRectF(rect).toRect()
            painter.drawPixmap(rect, icon.pixmap(rect.size()))  # 绘制像素图


class FluentFontIconBase(FluentIconBase):
    """ 字体图标基类（基于字体文件的图标实现） """

    _isFontLoaded = False  # 字体是否已加载
    fontId = None  # 字体ID
    fontFamily = None  # 字体家族名称
    _iconNames = {}  # 图标名称→字符映射表

    def __init__(self, char: str):
        """
        初始化字体图标
        
        Parameters
        ----------
        char: str
            图标对应的Unicode字符
        """
        super().__init__()
        self.char = char  # 存储图标字符
        self.lightColor = QColor(0, 0, 0)  # 浅色主题默认颜色（黑）
        self.darkColor = QColor(255, 255, 255)  # 深色主题默认颜色（白）
        self.isBold = False  # 默认不使用粗体
        self.loadFont()  # 加载字体文件

    @classmethod
    def fromName(cls, name: str):
        """
        通过图标名称创建字体图标实例
        
        Parameters
        ----------
        name: str
            图标名称（需在_iconNames中定义）
        
        Returns
        -------
        FluentFontIconBase
            字体图标实例
        """
        icon = cls("")  # 创建实例
        icon.char = cls._iconNames.get(name, "")  # 根据名称获取字符
        return icon

    def bold(self):
        """ 设置为粗体图标 """
        self.isBold = True
        return self  # 返回自身，支持链式调用

    def icon(self, theme=Theme.AUTO, color: QColor = None) -> QIcon:
        """ 重写icon方法，返回字体图标 """
        if not color:
            color = self._getIconColor(theme)  # 获取主题对应的颜色
        # 使用FontIconEngine创建图标
        return QIcon(FontIconEngine(self.fontFamily, self.char, color, self.isBold))

    def colored(self, lightColor, darkColor):
        """ 重写colored方法，设置自定义颜色 """
        self.lightColor = QColor(lightColor)
        self.darkColor = QColor(darkColor)
        return self

    def render(self, painter: QPainter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        """ 重写render方法，绘制字体图标 """
        color = self._getIconColor(theme)  # 获取主题颜色

        if "fill" in attributes:  # 如果指定了fill属性，优先使用
            color = QColor(attributes["fill"])

        # 配置字体
        font = QFont(self.fontFamily)
        font.setBold(self.isBold)
        font.setPixelSize(round(rect.height()))  # 字体大小=图标高度

        painter.setFont(font)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        # 绘制文本路径
        path = QPainterPath()
        path.addText(rect.x(), rect.y() + rect.height(), font, self.char)
        painter.drawPath(path)

    def iconNameMapPath(self) -> str:
        """ 返回图标名称-字符映射文件路径（子类实现） """
        return None

    def loadFont(self):
        """ 加载字体文件到应用 """
        cls = self.__class__
        # 如果已加载或应用未初始化，直接返回
        if cls._isFontLoaded or not QApplication.instance():
            return

        # 读取字体文件
        file = QFile(self.path())  # 调用path()获取字体文件路径
        if not file.open(QFile.ReadOnly):  # 打开失败抛出异常
            raise FileNotFoundError(f"Cannot open font file: {self.path()}")

        data = file.readAll()  # 读取字体数据
        file.close()

        # 将字体添加到应用
        cls.fontId = QFontDatabase.addApplicationFontFromData(data)
        cls.fontFamily = QFontDatabase.applicationFontFamilies(cls.fontId)[0]  # 获取字体家族名称

        # 加载图标名称映射（如果有）
        if self.iconNameMapPath():
            self.loadIconNames()

        cls._isFontLoaded = True  # 标记字体已加载

    def loadIconNames(self):
        """ 加载图标名称-字符映射表（从JSON文件） """
        cls = self.__class__
        cls._iconNames.clear()  # 清空现有映射

        # 读取映射文件
        file = QFile(self.iconNameMapPath())
        if not file.open(QFile.ReadOnly):
            raise FileNotFoundError(f"Cannot open font file: {self.iconNameMapPath()}")

        # 解析JSON并存储映射
        cls._iconNames = json.loads(str(file.readAll(), encoding='utf-8'))
        file.close()

    def _getIconColor(self, theme):
        """ 根据主题获取图标颜色（内部方法） """
        if theme == Theme.AUTO:
            color = self.darkColor if isDarkTheme() else self.lightColor
        else:
            color = self.darkColor if theme == Theme.DARK else self.lightColor
        return color

class ColoredFluentIcon(FluentIconBase):
    """ 支持自定义颜色的Fluent图标（浅色/深色主题分别设置） """

    def __init__(self, icon: FluentIconBase, lightColor, darkColor):
        """
        Parameters
        ----------
        icon: FluentIconBase
            原始Fluent图标
        
        lightColor: str | QColor | Qt.GlobalColor
            浅色主题图标颜色
        
        darkColor: str | QColor | Qt.GlobalColor
            深色主题图标颜色
        """
        super().__init__()
        self.fluentIcon = icon  # 存储原始图标
        self.lightColor = QColor(lightColor)  # 浅色主题颜色
        self.darkColor = QColor(darkColor)  # 深色主题颜色

    def path(self, theme=Theme.AUTO) -> str:
        """ 重写path方法，返回原始图标路径 """
        return self.fluentIcon.path(theme)

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        """ 重写render方法，应用自定义颜色 """
        icon = self.path(theme)  # 获取原始图标路径

        if not icon.endswith('.svg'):  # 非SVG图标直接渲染
            return self.fluentIcon.render(painter, rect, theme, indexes, attributes)

        # 确定当前主题颜色
        if theme == Theme.AUTO:
            color = self.darkColor if isDarkTheme() else self.lightColor
        else:
            color = self.darkColor if theme == Theme.DARK else self.lightColor

        # 应用颜色属性并绘制
        attributes.update(fill=color.name())  # 添加fill属性
        icon = writeSvg(icon, indexes, **attributes).encode()  # 修改SVG
        drawSvgIcon(icon, painter, rect)  # 绘制修改后的SVG

class FluentIcon(FluentIconBase, Enum):
    """ Fluent图标枚举（定义所有可用的Fluent风格图标） """

    # 枚举成员：名称 = "图标文件名前缀"（对应SVG文件）
    UP = "Up"
    ADD = "Add"
    BUS = "Bus"
    CAR = "Car"
    CUT = "Cut"
    IOT = "IOT"
    PIN = "Pin"
    TAG = "Tag"
    VPN = "VPN"
    CAFE = "Cafe"
    CHAT = "Chat"
    COPY = "Copy"
    CODE = "Code"
    DOWN = "Down"
    EDIT = "Edit"
    FLAG = "Flag"
    FONT = "Font"
    GAME = "Game"
    HELP = "Help"
    HIDE = "Hide"
    HOME = "Home"
    INFO = "Info"
    LEAF = "Leaf"
    LINK = "Link"
    MAIL = "Mail"
    MENU = "Menu"
    MUTE = "Mute"
    MORE = "More"
    MOVE = "Move"
    PLAY = "Play"
    SAVE = "Save"
    SEND = "Send"
    SYNC = "Sync"
    UNIT = "Unit"
    VIEW = "View"
    WIFI = "Wifi"
    ZOOM = "Zoom"
    ALBUM = "Album"
    BRUSH = "Brush"
    BROOM = "Broom"
    CLOSE = "Close"
    CLOUD = "Cloud"
    EMBED = "Embed"
    GLOBE = "Globe"
    HEART = "Heart"
    LABEL = "Label"
    MEDIA = "Media"
    MOVIE = "Movie"
    MUSIC = "Music"
    ROBOT = "Robot"
    PAUSE = "Pause"
    PASTE = "Paste"
    PHOTO = "Photo"
    PHONE = "Phone"
    PRINT = "Print"
    SHARE = "Share"
    TILES = "Tiles"
    UNPIN = "Unpin"
    VIDEO = "Video"
    TRAIN = "Train"
    ADD_TO  ="AddTo"
    ACCEPT = "Accept"
    CAMERA = "Camera"
    CANCEL = "Cancel"
    DELETE = "Delete"
    FOLDER = "Folder"
    FILTER = "Filter"
    MARKET = "Market"
    SCROLL = "Scroll"
    LAYOUT = "Layout"
    GITHUB = "GitHub"
    UPDATE = "Update"
    REMOVE = "Remove"
    RETURN = "Return"
    PEOPLE = "People"
    QRCODE = "QRCode"
    RINGER = "Ringer"
    ROTATE = "Rotate"
    SEARCH = "Search"
    VOLUME = "Volume"
    FRIGID  = "Frigid"
    SAVE_AS = "SaveAs"
    ZOOM_IN = "ZoomIn"
    CONNECT  ="Connect"
    HISTORY = "History"
    SETTING = "Setting"
    PALETTE = "Palette"
    MESSAGE = "Message"
    FIT_PAGE = "FitPage"
    ZOOM_OUT = "ZoomOut"
    AIRPLANE = "Airplane"
    ASTERISK = "Asterisk"
    CALORIES = "Calories"
    CALENDAR = "Calendar"
    FEEDBACK = "Feedback"
    LIBRARY = "BookShelf"
    MINIMIZE = "Minimize"
    CHECKBOX = "CheckBox"
    DOCUMENT = "Document"
    LANGUAGE = "Language"
    DOWNLOAD = "Download"
    QUESTION = "Question"
    SPEAKERS = "Speakers"
    DATE_TIME = "DateTime"
    FONT_SIZE = "FontSize"
    HOME_FILL = "HomeFill"
    PAGE_LEFT = "PageLeft"
    SAVE_COPY = "SaveCopy"
    SEND_FILL = "SendFill"
    SKIP_BACK = "SkipBack"
    SPEED_OFF = "SpeedOff"
    ALIGNMENT = "Alignment"
    BLUETOOTH = "Bluetooth"
    COMPLETED = "Completed"
    CONSTRACT = "Constract"
    HEADPHONE = "Headphone"
    MEGAPHONE = "Megaphone"
    PROJECTOR = "Projector"
    EDUCATION = "Education"
    LEFT_ARROW = "LeftArrow"
    ERASE_TOOL = "EraseTool"
    PAGE_RIGHT = "PageRight"
    PLAY_SOLID = "PlaySolid"
    BOOK_SHELF = "BookShelf"
    HIGHTLIGHT = "Highlight"
    FOLDER_ADD = "FolderAdd"
    PAUSE_BOLD = "PauseBold"
    PENCIL_INK = "PencilInk"
    PIE_SINGLE = "PieSingle"
    QUICK_NOTE = "QuickNote"
    SPEED_HIGH = "SpeedHigh"
    STOP_WATCH = "StopWatch"
    ZIP_FOLDER = "ZipFolder"
    BASKETBALL = "Basketball"
    BRIGHTNESS = "Brightness"
    DICTIONARY = "Dictionary"
    MICROPHONE = "Microphone"
    ARROW_DOWN = "ChevronDown"
    FULL_SCREEN = "FullScreen"
    MIX_VOLUMES = "MixVolumes"
    REMOVE_FROM = "RemoveFrom"
    RIGHT_ARROW = "RightArrow"
    QUIET_HOURS  ="QuietHours"
    FINGERPRINT = "Fingerprint"
    APPLICATION = "Application"
    CERTIFICATE = "Certificate"
    TRANSPARENT = "Transparent"
    IMAGE_EXPORT = "ImageExport"
    SPEED_MEDIUM = "SpeedMedium"
    LIBRARY_FILL = "LibraryFill"
    MUSIC_FOLDER = "MusicFolder"
    POWER_BUTTON = "PowerButton"
    SKIP_FORWARD = "SkipForward"
    CARE_UP_SOLID = "CareUpSolid"
    ACCEPT_MEDIUM = "AcceptMedium"
    CANCEL_MEDIUM = "CancelMedium"
    CHEVRON_RIGHT = "ChevronRight"
    CLIPPING_TOOL = "ClippingTool"
    SEARCH_MIRROR = "SearchMirror"
    SHOPPING_CART = "ShoppingCart"
    FONT_INCREASE = "FontIncrease"
    BACK_TO_WINDOW = "BackToWindow"
    COMMAND_PROMPT = "CommandPrompt"
    CLOUD_DOWNLOAD = "CloudDownload"
    DICTIONARY_ADD = "DictionaryAdd"
    CARE_DOWN_SOLID = "CareDownSolid"
    CARE_LEFT_SOLID = "CareLeftSolid"
    CLEAR_SELECTION = "ClearSelection"
    DEVELOPER_TOOLS = "DeveloperTools"
    BACKGROUND_FILL = "BackgroundColor"
    CARE_RIGHT_SOLID = "CareRightSolid"
    CHEVRON_DOWN_MED = "ChevronDownMed"
    CHEVRON_RIGHT_MED = "ChevronRightMed"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"
    EXPRESSIVE_INPUT_ENTRY = "ExpressiveInputEntry"

    def path(self, theme=Theme.AUTO) -> str:
        """ 获取图标文件路径（重写FluentIconBase的path方法） """
        color = getIconColor(theme)  # 获取主题对应的颜色（"black"或"white"）
        return f':/resource/images/icons/{self.value}_{color}.svg'


class Icon(QIcon):
    """ 图标包装类（将FluentIcon转换为QIcon，并支持主题同步） """

    def __init__(self, fluentIcon: FluentIcon):
        """
        Parameters
        ----------
        fluentIcon: FluentIcon
            Fluent图标枚举成员
        """
        super().__init__(fluentIcon.qicon())  # 使用FluentIcon的qicon()方法创建QIcon
        self.fluentIcon = fluentIcon  # 存储原始FluentIcon


def toQIcon(icon: Union[QIcon, FluentIconBase, str]) -> QIcon:
    """
    将图标转换为QIcon（统一图标类型）
    
    Parameters
    ----------
    icon: QIcon | FluentIconBase | str
        输入图标（QIcon对象、Fluent图标或路径字符串）
    
    Returns
    -------
    QIcon
        转换后的QIcon对象
    """
    if isinstance(icon, str):
        return QIcon(icon)  # 字符串→QIcon（路径）
    elif isinstance(icon, FluentIconBase):
        return icon.qicon()  # Fluent图标→QIcon（主题同步）
    return icon  # QIcon直接返回


class Action(QAction):
    """ 支持Fluent图标的QAction（动作项） """

    @singledispatchmethod
    def __init__(self, parent: QObject = None, **kwargs):
        """ 多构造函数：无文本无图标 """
        super().__init__(parent, **kwargs)
        self.fluentIcon = None  # 存储Fluent图标

    @__init__.register
    def _(self, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带文本 """
        super().__init__(text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带QIcon和文本 """
        super().__init__(icon, text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带Fluent图标和文本 """
        super().__init__(icon.icon(), text, parent, **kwargs)  # 使用Fluent图标
        self.fluentIcon = icon  # 存储Fluent图标

    @__init__.register
    def _(self, icon: QIcon, parent: QObject = None, **kwargs):
        """ 多构造函数：带QIcon """
        super().__init__(icon, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QObject = None, **kwargs):
        """ 多构造函数：带Fluent图标 """
        super().__init__(icon.icon(), parent, **kwargs)  # 使用Fluent图标
        self.fluentIcon = icon  # 存储Fluent图标



    def icon(self) -> QIcon:
        """ 重写icon方法，返回Fluent图标（主题同步） """
        if self.fluentIcon:
            return Icon(self.fluentIcon)  # 返回包装后的QIcon
        return super().icon()  # 否则返回默认QIcon

    def setIcon(self, icon: Union[FluentIconBase, QIcon]):
        """ 设置图标（支持Fluent图标或QIcon） """
        if isinstance(icon, FluentIconBase):
            self.fluentIcon = icon  # 存储Fluent图标
            icon = icon.icon()  # 转换为QIcon
        super().setIcon(icon)  # 调用父类方法设置图标