
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal,QObject,pyqtSlot
import os
from enum import Enum
import threading
from typing import List
from PyQt5.QtCore import pyqtSignal,QThread
from natsort import natsorted
from collections import OrderedDict 




# coding:utf-8
# 导入数学向下取整函数，用于数值计算
from math import floor
# 导入字节流处理模块，用于内存中字节数据操作
from io import BytesIO
# 导入类型注解工具，用于函数参数和返回值类型标注
from typing import Union

# 导入numpy库，用于图像处理的数组操作
import numpy as np
# 导入colorthief库，用于提取图像主色调
from colorthief import ColorThief
# 导入PIL库的Image模块，用于PIL图像对象操作
from PIL import Image
# 导入PyQt5的图像类，用于Qt图像对象操作
from PyQt5.QtGui import QImage, QPixmap
# 导入PyQt5的核心模块，用于缓冲区和I/O设备操作
from PyQt5.QtCore import QIODevice, QBuffer
# 导入scipy的高斯滤波函数，用于图像模糊处理
from scipy.ndimage.filters import gaussian_filter

# 导入异常处理装饰器，用于捕获并处理函数执行中的异常

def gaussianBlur(image, blurRadius=18, brightFactor=1, blurPicSize=None):
    """
    对图像应用高斯模糊处理
    
    参数:
        image: 输入图像，可为文件路径字符串或QPixmap/QImage对象
        blurRadius: 高斯模糊半径，值越大模糊效果越强，默认18
        brightFactor: 亮度调整因子，用于调整模糊后图像的亮度，默认1(不调整)
        blurPicSize: 元组(int, int)，模糊前调整图像尺寸以优化性能，默认None(不调整)
    
    返回:
        QPixmap: 处理后的模糊图像
    """
    # 判断输入图像类型，若为字符串且非Qt资源路径，则打开为PIL图像
    if isinstance(image, str) and not image.startswith(':'):
        image = Image.open(image)
    # 否则，调用fromqpixmap函数将QPixmap/QImage转换为PIL图像
    else:
        image = fromqpixmap(QPixmap(image))

    # 若指定了模糊前的图像尺寸，则调整图像大小以减少计算量
    if blurPicSize:
        # 获取原图像尺寸
        w, h = image.size
        # 计算宽高缩放比例，取宽和高中较小的比例以保持图像比例
        ratio = min(blurPicSize[0] / w, blurPicSize[1] / h)
        # 计算调整后的尺寸
        w_, h_ = w * ratio, h * ratio

        # 若调整后的宽度小于原宽度，则执行缩放(使用抗锯齿模式)
        if w_ < w:
            image = image.resize((int(w_), int(h_)), Image.ANTIALIAS)

    # 将PIL图像转换为numpy数组，以便进行数值处理
    image = np.array(image)

    # 处理灰度图像：若图像为二维数组(单通道)，则堆叠为三通道(RGB)
    if len(image.shape) == 2:
        image = np.stack([image, image, image], axis=-1)

    # 对每个颜色通道(0:R, 1:G, 2:B)分别应用高斯滤波
    for i in range(3):
        # 对第i通道执行高斯滤波，并用亮度因子调整像素值
        image[:, :, i] = gaussian_filter(
            image[:, :, i], blurRadius) * brightFactor

    # 获取处理后图像的高度、宽度和通道数
    h, w, c = image.shape
    # 根据通道数设置QImage格式(RGB888为3通道，RGBA8888为4通道)
    if c == 3:
        format = QImage.Format_RGB888
    else:
        format = QImage.Format_RGBA8888

    # 将numpy数组转换为QImage，再转换为QPixmap返回
    return QPixmap.fromImage(QImage(image.data, w, h, c*w, format))


def fromqpixmap(im: Union[QImage, QPixmap]):
    """
    将QImage或QPixmap对象转换为PIL Image对象
    
    参数:
        im: 输入图像对象，可为QImage或QPixmap
    
    返回:
        PIL.Image: 转换后的PIL图像对象
    """
    # 创建Qt缓冲区对象，用于临时存储图像数据
    buffer = QBuffer()
    # 以读写模式打开缓冲区
    buffer.open(QIODevice.ReadWrite)

    # 检查图像是否包含alpha通道(透明通道)
    if im.hasAlphaChannel():
        # 含透明通道时保存为png格式(保留alpha通道)
        im.save(buffer, "png")
    else:
        # 不含透明通道时保存为ppm格式(更适合PIL打开)
        im.save(buffer, "ppm")

    # 创建字节流对象，用于存储缓冲区数据
    b = BytesIO()
    # 将缓冲区数据写入字节流
    b.write(buffer.data())
    # 关闭缓冲区，释放资源
    buffer.close()
    # 将字节流指针移至起始位置，以便读取
    b.seek(0)

    # 从字节流中打开图像，返回PIL Image对象
    return Image.open(b)


class DominantColor:
    """ 
    主色调提取类，用于从图像中提取主导颜色 
    """

    @classmethod
    def getDominantColor(cls, imagePath):
        """
        从图像中提取主色调
        
        参数:
            imagePath: str，图像文件路径
        
        返回:
            (r, g, b): 元组，主色调的RGB通道灰度值(0-255)
        """
        # 若图像路径为Qt资源路径(以:开头)，返回默认深灰色(24,24,24)
        if imagePath.startswith(':'):
            return (24, 24, 24)

        # 创建ColorThief对象，用于提取主色调
        colorThief = ColorThief(imagePath)

        # 若图像最大边长超过400像素，缩放到400x400以加快计算速度
        if max(colorThief.image.size) > 400:
            colorThief.image = colorThief.image.resize((400, 400))

        # 提取图像调色板(quality=9表示降低采样质量以提高速度)
        palette = colorThief.get_palette(quality=9)

        # 调整调色板颜色的亮度
        palette = cls.__adjustPaletteValue(palette)
        # 遍历调色板，移除接近红色的颜色(色相h<0.02视为红色系)
        for rgb in palette[:]:
            h, s, v = cls.rgb2hsv(rgb)
            if h < 0.02:
                palette.remove(rgb)
                # 若调色板剩余颜色少于等于2种，停止移除
                if len(palette) <= 2:
                    break

        # 取调色板前5种颜色
        palette = palette[:5]
        # 按颜色鲜艳度从高到低排序
        palette.sort(key=lambda rgb: cls.colorfulness(*rgb), reverse=True)

        # 返回最鲜艳的颜色(排序后第一个)
        return palette[0]

    @classmethod
    def __adjustPaletteValue(cls, palette):
        """
        调整调色板颜色的亮度(私有类方法)
        
        参数:
            palette: 列表，[(r,g,b), ...]，待调整的颜色列表
        
        返回:
            newPalette: 列表，[(r,g,b), ...]，调整亮度后的颜色列表
        """
        newPalette = []
        # 遍历调色板中的每个颜色
        for rgb in palette:
            # 将RGB转换为HSV颜色空间(h:色相, s:饱和度, v:明度)
            h, s, v = cls.rgb2hsv(rgb)
            # 根据明度v调整亮度因子: 明度越高，降低越多以避免过亮
            if v > 0.9:
                factor = 0.8
            elif 0.8 < v <= 0.9:
                factor = 0.9
            elif 0.7 < v <= 0.8:
                factor = 0.95
            else:
                factor = 1  # 明度适中或较低时不调整
            # 应用亮度因子调整明度
            v *= factor
            # 将调整后的HSV转换回RGB，添加到新调色板
            newPalette.append(cls.hsv2rgb(h, s, v))

        return newPalette

    @staticmethod
    def rgb2hsv(rgb):
        """
        将RGB颜色转换为HSV颜色空间(静态方法)
        
        参数:
            rgb: 元组，(r,g,b)，RGB通道值(0-255)
        
        返回:
            (h, s, v): 元组，h(色相0-360), s(饱和度0-1), v(明度0-1)
        """
        # 将RGB值归一化到0-1范围
        r, g, b = [i / 255 for i in rgb]
        # 获取RGB中的最大值(明度基础)和最小值
        mx = max(r, g, b)
        mn = min(r, g, b)
        # 计算最大最小差值(用于计算饱和度和色相)
        df = mx - mn
        # 计算色相h: 若RGB值相等(灰度)，h=0
        if mx == mn:
            h = 0
        # 若红色为最大值，h在0-60或300-360范围
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        # 若绿色为最大值，h在60-120范围
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        # 若蓝色为最大值，h在240-300范围
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        # 计算饱和度s: 若明度为0(黑色)，s=0；否则为df/mx
        s = 0 if mx == 0 else df / mx
        # 明度v即为最大值mx
        v = mx
        return (h, s, v)

    @staticmethod
    def hsv2rgb(h, s, v):
        """
        将HSV颜色转换为RGB颜色空间(静态方法)
        
        参数:
            h: 色相(0-360)
            s: 饱和度(0-1)
            v: 明度(0-1)
        
        返回:
            (r, g, b): 元组，RGB通道值(0-255)
        """
        # 将色相转换为60度为单位的数值
        h60 = h / 60.0
        # 获取h60的整数部分(用于判断色相区间)
        h60f = floor(h60)
        # 色相区间索引(0-5)
        hi = int(h60f) % 6
        # 色相区间内的小数部分(用于插值计算)
        f = h60 - h60f
        # 根据HSV计算中间值p、q、t(用于不同区间的RGB转换)
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        # 初始化RGB值
        r, g, b = 0, 0, 0
        # 根据色相区间计算RGB值
        if hi == 0:
            r, g, b = v, t, p
        elif hi == 1:
            r, g, b = q, v, p
        elif hi == 2:
            r, g, b = p, v, t
        elif hi == 3:
            r, g, b = p, q, v
        elif hi == 4:
            r, g, b = t, p, v
        elif hi == 5:
            r, g, b = v, p, q
        # 将RGB值从0-1范围转换为0-255整数
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return (r, g, b)

    @staticmethod
    def colorfulness(r: int, g: int, b: int):
        """
        计算颜色的鲜艳度(静态方法)
        
        参数:
            r, g, b: 整数，RGB通道值(0-255)
        
        返回:
            float: 鲜艳度值，值越大颜色越鲜艳
        """
        # 计算RG通道差异的绝对值
        rg = np.absolute(r - g)
        # 计算黄蓝通道差异的绝对值(基于RGB转换为YIQ颜色空间的Y和B分量近似)
        yb = np.absolute(0.5 * (r + g) - b)

        # 计算rg和yb的均值与标准差
        rg_mean, rg_std = (np.mean(rg), np.std(rg))
        yb_mean, yb_std = (np.mean(yb), np.std(yb))

        # 组合标准差和均值的平方根，作为鲜艳度指标
        std_root = np.sqrt((rg_std ** 2) + (yb_std ** 2))
        mean_root = np.sqrt((rg_mean ** 2) + (yb_mean ** 2))

        # 返回鲜艳度值(标准差分量 + 0.3*均值分量)
        return std_root + (0.3 * mean_root)






class ImageExtension(Enum):
    PNG = ".png"
    JPG = ".jpg"
    JPEG = ".jpeg"
    BMP = ".bmp"
    GIF = ".gif"
    TIFF = ".tiff"
    WEBP = ".webp"
    SVG = ".svg"
    JFIF = ".jfif"

    @classmethod
    def get_values(cls) -> List[str]:
        return [ext.value for ext in cls]

def get_image_paths(dir_path: str) -> List[str]:
    """
    获取目录下所有图片文件的文件名（包括子目录）。
    :param path: 目录路径
    :return: 图片文件名列表
    """
    image_filenames = []
    supported_formats = ImageExtension.get_values()
    with os.scandir(dir_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.lower().endswith(tuple(supported_formats)):
                image_filenames.append(entry.path)

    image_filenames = natsorted(image_filenames)

    return image_filenames

class LRUCache:
    """
    LRU缓存实现类，用于缓存最近使用的图片。
    当缓存满时，会移除最近最少使用的项。
    """
    def __init__(self, capacity: int = 300):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):

        if key not in self.cache:
            return None
        
        self.cache.move_to_end(key)

        return self.cache[key]

    def put(self, key: str, value: QPixmap): 
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        self.cache.clear()

class PreloadWorker(QThread):
    """
    预加载线程，用于异步加载图片文件。
    """

    progress = pyqtSignal(str, QPixmap)
    finished = pyqtSignal()
    
    def __init__(self, image_paths: list):
        super().__init__()
        self.image_paths = image_paths
        self.is_running = True
        self._stop_event = threading.Event()

    def run(self):
        for path in self.image_paths:

            if self._stop_event.is_set():
                break
            
            pixmap = self._load_image(path)
            
            if pixmap:
                self.progress.emit(path, pixmap)

        self.finished.emit()

    def _load_image(self, path) -> QPixmap:
        try:
            image = QImage(path)
            if image.isNull():
                return None
            return QPixmap.fromImage(image)
        except Exception as e:
            print(f"预加载失败: {path}, 错误: {e}")
            return None

    def stop(self):
        self._stop_event.set()

class AbstractViewer(QObject):
    """
    抽象的“查看器”模型。负责管理一个列表和当前索引，并提供浏览接口。
    当状态变化时，通过信号通知视图。
    
    """

    current_item_changed = pyqtSignal()  # 当前项改变时触发
    item_deleted = pyqtSignal(int)             # 项被删除时触发，传递被删除的索引
    item_inserted = pyqtSignal(int)            # 项被插入时触发，传递插入的索引
    model_reset = pyqtSignal()                 # 模型数据被重置时触发 (例如 clear 或 set_items)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._current_index = -1

    @property
    def items(self):
        return self._items.copy()

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def current_item(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    @property
    def count(self) -> int:
        return len(self._items)

    def set_items(self, items):
        if not isinstance(items, (list, tuple)):
            raise TypeError("items 必须是一个列表或元组。")

        self._items = list(items)
        self._current_index = 0 if self._items else -1
        self.model_reset.emit()
        if self._items:
            self.current_item_changed.emit()

    def insert_item(self, index: int, item):

        if not (0 <= index <= self.count):
            index = self.count

        self._items.insert(index, item)

        if index <= self._current_index:
            self._current_index += 1
            self.current_item_changed.emit()

        self.item_inserted.emit(index)

    def clear(self):
        if self._items:
            self._items.clear()
            self._current_index = -1
            self.model_reset.emit()
    

    def next(self):
        if self._current_index < len(self._items) - 1:
            self.go_to(self._current_index + 1)

    def previous(self):
        if self._current_index > 0:
            self.go_to(self._current_index - 1)

    def go_to(self, index: int):

        if not isinstance(index, int):
            raise TypeError("index 必须是整数。")

        if 0 <= index < self.count and index != self._current_index:
            self._current_index = index
            self.current_item_changed.emit()

    def delete_current(self):
        if self._current_index == -1:
            return

        deleted_index = self._current_index

        del self._items[deleted_index]

        if deleted_index < len(self._items):
            new_index = deleted_index
        else:
            new_index = len(self._items) - 1 

        self._current_index = new_index
        self.current_item_changed.emit()

        self.item_deleted.emit(deleted_index)

class ImageManager(AbstractViewer):
    
    image_loaded = pyqtSignal(QPixmap)

    def __init__(self, parent=None, batch_size=100):
        super().__init__(parent)
        
        self._preload_worker = None
        self._batch_size = batch_size
        self._pixmap_cache = LRUCache(capacity=batch_size*2)

        self.current_item_changed.connect(self._get_current_image)
        self.current_item_changed.connect(self._preload_next_batch)
        
    def set_items(self, items):
        super().set_items(items)
        self._pixmap_cache.clear()
        self._stop_preload()
        
    def delete_current(self):
        super().delete_current()
        self._pixmap_cache.delete(self.current_item)
    
    def _get_current_image(self) -> QPixmap:
        if not self.items or self.current_index == -1:
            return None

        path = self.items[self.current_index]
        
        pixmap = self._pixmap_cache.get(path)

        if not pixmap:
        
            pixmap = QPixmap(path)

            if not pixmap:
                return None
      
            self._pixmap_cache.put(path, pixmap)

        self.image_loaded.emit(pixmap)
    
    def _stop_preload(self):
        if self._preload_worker and self._preload_worker.isRunning():
            self._preload_worker.stop()
            self._preload_worker.wait()

    def _preload_next_batch(self):
        
        next_batch_start = self.current_index+1
        next_batch_end = min(next_batch_start + self._batch_size, self.count)
        current_batch_paths = self.items[next_batch_start:next_batch_end]

        paths_to_preload = [p for p in current_batch_paths if p not in self._pixmap_cache.cache.keys()]

        if paths_to_preload:
    
            self._stop_preload()
            
            self._preload_worker = PreloadWorker(paths_to_preload)
            self._preload_worker.signals.progress.connect(self._on_image_preloaded)
    
            self._preload_worker.start()
    
    @pyqtSlot(str, QPixmap)
    def _on_image_preloaded(self, path: str, pixmap: QPixmap):
        """ 预加载线程完成信号槽函数：处理预加载完成后的缓存更新 """
        if pixmap:
            self._pixmap_cache.put(path, pixmap)

    def closeEvent(self, event):
        self._stop_preload()
        event.accept()