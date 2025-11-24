# coding:utf-8
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal,QObject,pyqtSlot
import os
from enum import Enum
import threading
from typing import List
from PyQt5.QtCore import pyqtSignal,QThread
from natsort import natsorted
from collections import OrderedDict 


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
            self._preload_worker.progress.connect(self._on_image_preloaded)
    
            self._preload_worker.start()
    
    @pyqtSlot(str, QPixmap)
    def _on_image_preloaded(self, path: str, pixmap: QPixmap):
        """ 预加载线程完成信号槽函数：处理预加载完成后的缓存更新 """
        if pixmap:
            self._pixmap_cache.put(path, pixmap)

    def closeEvent(self, event):
        self._stop_preload()
        event.accept()