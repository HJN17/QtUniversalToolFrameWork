# coding:utf-8
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal,pyqtSlot
import os
from enum import Enum
import threading
from typing import List
from PyQt5.QtCore import pyqtSignal,QThread
from natsort import natsorted
from .abstract import AbstractViewer
from .cache import LRUCache

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


class ImageManager(AbstractViewer):
    
    image_loaded = pyqtSignal(QPixmap)

    def __init__(self, parent=None, batch_size=100):
        super().__init__(parent)
        
        self._preload_worker = None
        self._batch_size = batch_size
        self._pixmap_cache = LRUCache(capacity=batch_size*2)

        self.current_item_changed.connect(self._get_current_image)
        self.current_item_changed.connect(self._preload_next_batch)
        


    def get_image_name_by_index(self,index:int) -> str:
        if index < 0 or index >= self.count:
            return ""
        return os.path.basename(self.items[index]).split(".")[0]
    
    def get_image_name_by_current_index(self) -> str:
        return self.get_image_name_by_index(self.current_index)

    

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
