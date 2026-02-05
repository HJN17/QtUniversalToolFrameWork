# coding:utf-8
import json
import os
from copy import deepcopy
from enum import Enum 
from pathlib import Path 
from typing import List

import darkdetect  # 导入系统主题检测库，用于自动识别系统深色/浅色主题
from PyQt5.QtCore import QObject, pyqtSignal,QSettings,QCoreApplication,QFileInfo
from PyQt5.QtGui import QColor

class Theme(Enum):
    LIGHT = "Light" 
    DARK = "Dark"  
    AUTO = "Auto"


class ConfigValidator:
    """ 配置验证器基类：定义配置值的验证和修正接口 """

    def validate(self, value): # 验证配置值是否合法
        return True

    def correct(self, value): # 修正非法配置值（基类默认返回原值）
        return value

class RangeValidator(ConfigValidator):
    """ 范围验证器：验证值是否在指定范围内，并修正超出范围的值 """
    def __init__(self, min, max):
        self.min = min  
        self.max = max 
        self.range = (min, max) 

    def validate(self, value):
        return self.min <= value <= self.max

    def correct(self, value):
        return min(max(self.min, value), self.max)

class OptionsValidator(ConfigValidator):
    """ 选项验证器：验证值是否在预定义选项列表中，并修正为默认选项（若非法） """

    def __init__(self, options):
        if not options:
            raise ValueError("The `options` can't be empty.") 

        if isinstance(options, Enum):
            options = options._member_map_.values() # 获取枚举成员值列表

        self.options = list(options) 

    def validate(self, value):
        return value in self.options

    def correct(self, value):
        return value if self.validate(value) else self.options[0]


class ThemeValidator(OptionsValidator):
    """ 主题验证器：限定值只能为Theme枚举成员（继承自选项验证器） """

    def correct(self, value):
        
        if self.validate(value):

            if value == Theme.AUTO:
                return Theme(darkdetect.theme())
            else:
                return value

        return Theme.LIGHT

class BoolValidator(OptionsValidator):
    """ 布尔值验证器：限定值只能为True或False（继承自选项验证器） """

    def __init__(self):
        super().__init__([True, False])

class FolderValidator(ConfigValidator):
    """ 文件夹路径验证器：验证路径是否存在，并自动创建不存在的文件夹 """

    def validate(self, value):
        return Path(value).exists()

    def correct(self, value):
        path = Path(value)
        path.mkdir(exist_ok=True, parents=True) 
        return str(path.absolute()).replace("\\", "/")

class FolderListValidator(ConfigValidator):
    """ 文件夹列表验证器：验证列表中的所有路径是否存在，并过滤无效路径 """

    def validate(self, value):
        return all(Path(i).exists() for i in value)

    def correct(self, value: List[str]):
        folders = []
        for folder in value:
            path = Path(folder)
            if path.exists():
                folders.append(str(path.absolute()).replace("\\", "/")) 

        return folders

class ColorValidator(ConfigValidator):
    """ RGB颜色验证器：验证颜色值是否合法，并修正为默认颜色（若非法） """

    def __init__(self, default):
        self.default = QColor(default)  # 存储默认颜色（转换为QColor对象）

    def validate(self, color):
        try:
            return QColor(color).isValid()  # 尝试转换并检查有效性
        except:
            return False

    def correct(self, value):
        """若颜色非法，返回默认颜色；否则返回转换后的QColor对象"""
        return QColor(value) if self.validate(value) else self.default
    

class ConfigSerializer:
    """ 配置序列化器基类：定义配置值的序列化和反序列化接口 """

    def serialize(self, value):
        return value

    def deserialize(self, value): 
        return value 

class EnumSerializer(ConfigSerializer):
    """ 枚举序列化器：处理枚举类型与字符串的相互转换 """

    def __init__(self, enumClass):
        self.enumClass = enumClass

    def serialize(self, value):
        return value.value

    def deserialize(self, value):
        return self.enumClass(value)

class ColorSerializer(ConfigSerializer):
    """ QColor序列化器：处理QColor与字符串/列表的相互转换 """

    def serialize(self, value: QColor):
        return value.name(QColor.HexArgb)

    def deserialize(self, value):
        if isinstance(value, list):
            return QColor(*value)
        return QColor(value)


class ConfigItem(QObject):
    """ 配置项类：表示单个配置项，包含值、验证器、序列化器等 """

    valueChanged = pyqtSignal(object)

    def __init__(self, group, name, default, validator=None, serializer=None, restart=False):
        super().__init__()
        self.group = group
        self.name = name
        self.validator = validator or ConfigValidator()
        self.serializer = serializer or ConfigSerializer() 
        self.__value = default 
        self.defaultValue = self.validator.correct(default) 
        self.value = default  # 通过setter触发验证和修正
        self.restart = restart  # 存储是否需要重启
        

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, v):
        v = self.validator.correct(v) 
        ov = self.__value
        self.__value = v 
        if ov != v:
            self.valueChanged.emit(v)

    @property
    def key(self):
        return self.group+"_"+self.name if self.name else self.group

    def __str__(self):
        return f'{self.__class__.__name__}[value={self.value}]'

    def serialize(self):
        return self.serializer.serialize(self.value)

    def deserializeFrom(self, value): # 从JSON值反序列化配置项值
        self.value = self.serializer.deserialize(value)

class RangeConfigItem(ConfigItem):
    """ 范围配置项类：扩展ConfigItem，增加range属性（适用于RangeValidator） """

    @property
    def range(self):
        return self.validator.range

    def __str__(self):
        return f'{self.__class__.__name__}[range={self.range}, value={self.value}]'

class OptionsConfigItem(ConfigItem):
    """ 选项配置项类：扩展ConfigItem，增加options属性（适用于OptionsValidator） """

    @property
    def options(self):
        return self.validator.options

    def __str__(self):
        return f'{self.__class__.__name__}[options={self.options}, value={self.value}]'

class ColorConfigItem(ConfigItem):
    """ 颜色配置项类：专门用于颜色配置，默认使用ColorValidator和ColorSerializer """

    def __init__(self, group, name, default, restart=False):
        
        super().__init__(group, name, QColor(default), ColorValidator(default),
                         ColorSerializer(), restart)

    def __str__(self):
     
        return f'{self.__class__.__name__}[value={self.value.name()}]'


class QConfig(QObject):
    """ 应用配置管理类：管理所有配置项，处理配置的加载、保存、主题切换等 """

    appRestartSig = pyqtSignal()
    themeChanged = pyqtSignal(Theme)
    themeColorChanged = pyqtSignal(QColor)

    themeMode = OptionsConfigItem("QFluentWidgets", "ThemeMode", Theme.LIGHT, ThemeValidator(Theme), EnumSerializer(Theme))

    themeColor = ColorConfigItem("QFluentWidgets", "ThemeColor", "#d76603")
    
    #downloadFolder = ConfigItem("Folders", "Download", "resources/download/", FolderValidator())
    
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)

    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    def __init__(self):
        super().__init__()

        set = QSettings(QSettings.IniFormat, QSettings.UserScope, AUTHOR, "QtUniversalToolFrameWork") # 配置文件路径
        set_dir = QFileInfo(set.fileName()).absolutePath()  # 提取目录路径
        
        print(f"\n📍 配置文件存储路径: \033[32m{set_dir}\033[0m")

        if not set.contains("Config"):
            set.setValue("Config", "config.json") 

        self.file = os.path.join(set_dir, set.value("Config")) # 配置文件路径

    def filePath(self):
        return self.file

    def get(self, item):
        return item.value

    def set(self, item, value, save=True, copy=True):

        if item.value == value:
            return

        try:
            item.value = deepcopy(value) if copy else value
        except:
            item.value = value  # 深拷贝失败时直接赋值

        if save:
            self.save()

        if item.restart: # 若配置项需要重启，触发重启信号
            self.appRestartSig.emit()

        if item is self.themeMode: 
            self.themeChanged.emit(value) 

        if item is self.themeColor:
            self.themeColorChanged.emit(value)

    def toDict(self, serialize=True):
    
        items = {}
    

        all_attr_names = set(dir(self.__class__)) | set(dir(self))

        for name in all_attr_names: # 遍历类的所有属性
            try:
                item = getattr(self, name)
            except AttributeError:
            # 若实例无该属性，再从类获取
                item = getattr(self.__class__, name)
        
            if not isinstance(item, ConfigItem):
                continue

            value = item.serialize() if serialize else item.value
        
            if not items.get(item.group):  # 若group不存在，创建
                if not item.name:  # 若配置项无name，直接存储在group下
                    items[item.group] = value
                else: 
                    items[item.group] = {}

            if item.name:  # 将值存储在group.name下
                items[item.group][item.name] = value

        return items

    

    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, ensure_ascii=False, indent=4)


    def load(self, file=None):

        if isinstance(file, (str, Path)):
            self.file = Path(file)

        try: 
            with open(self.file, encoding="utf-8") as f:
                cfg = json.load(f) 
        except: 
            cfg = {}

        # 构建配置项键与实例的映射（键格式："group.name"）
        items = {}
        all_attr_names = set(dir(self.__class__)) | set(dir(self))
        for name in all_attr_names:
            
            try:
                item = getattr(self, name)
            except AttributeError:
                item = getattr(self.__class__, name)
                
            if isinstance(item, ConfigItem):
                items[item.key] = item 

        for k, v in cfg.items():
            if not isinstance(v, dict) and items.get(k) is not None:
                items[k].deserializeFrom(v)
            elif isinstance(v, dict):
                for key, value in v.items():
                    key = k + "_" + key
                    if items.get(key) is not None:
                        items[key].deserializeFrom(value)

      
    def addConfigItem(self, item):
        setattr(self.__class__, item.key, item)


def isDarkTheme():
    return qconfig.get(qconfig.themeMode) == Theme.DARK

def theme():
    return qconfig.get(qconfig.themeMode)

def isDarkThemeMode(theme=Theme.AUTO):
    return theme == Theme.DARK if theme != Theme.AUTO else isDarkTheme()



AUTHOR = "HJN"
VERSION = "0.3.2"

qconfig = QConfig()





