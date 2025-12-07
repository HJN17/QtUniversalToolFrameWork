from enum import Enum
from typing import Dict, Tuple, Optional, Union
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtCore import Qt, QPoint


class CursorStyle(Enum):
    CROSS = "Cross" 
    # 可扩展其他光标样式
    # C_HAND = "Hand"
    # C_ARROW = "Arrow"

    @property
    def path(self) -> str:
       
        return f':/resource/images/cursor/{self.value}.svg'

    def get_scaled_pixmap(self, size: int = 24) -> QPixmap:
        

        pixmap = QPixmap(self.path)

        if pixmap.isNull():
            print(f"Failed to load cursor image: {self.path}")
            return None
        
        # 保持比例缩放，抗锯齿
        return pixmap.scaled(
            size, size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )


class CursorManager:
   
    _HOT_SPOT_MAP: Dict[CursorStyle, Tuple[int, int]] = {
        CursorStyle.CROSS: (8, 8),
        
    }

    def __init__(self, default_size: int = 24):
        """
        初始化光标管理器
        :param default_size: 默认光标尺寸
        """
        self._default_size: int = default_size
        self._cursor_cache: Dict[Tuple[CursorStyle, int], QCursor] = {}

    def create_custom_cursor(self,cursor_style: CursorStyle,size: Optional[int] = None, use_cache: bool = True) -> QCursor:

        target_size = size or self._default_size

        cache_key = (cursor_style, target_size)

        if use_cache and cache_key in self._cursor_cache:
            return self._cursor_cache[cache_key]

        hot_spot_x, hot_spot_y = self._HOT_SPOT_MAP.get(cursor_style, (8, 8))
        hot_spot = QPoint(hot_spot_x, hot_spot_y)

        pixmap = cursor_style.get_scaled_pixmap(target_size)

        #print(f"cursor_style: {cursor_style}, size: {size}, use_cache: {use_cache}, hot_spot: {hot_spot}, pixmap: {pixmap}")

        if not pixmap:
            return QCursor(Qt.ArrowCursor)


        custom_cursor = QCursor(pixmap, hot_spot.x(), hot_spot.y())

        if use_cache:
            self._cursor_cache[cache_key] = custom_cursor

        return custom_cursor

    def set_widget_cursor(self,widget: QWidget, cursor_style: Union[CursorStyle, Qt.CursorShape, QCursor], size: Optional[int] = None) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError(f"Expected QWidget, got {type(widget).__name__}")
        
        if isinstance(cursor_style, CursorStyle):
            cursor = self.create_custom_cursor(cursor_style, size)
        elif isinstance(cursor_style, Qt.CursorShape):
            cursor = QCursor(cursor_style)
        elif isinstance(cursor_style, QCursor):
            cursor = cursor_style
        else:
            raise TypeError(
                f"cursor_style must be CursorStyle/Qt.CursorShape/QCursor, "
                f"got {type(cursor_style).__name__}"
            )
        widget.setCursor(cursor)

    def set_global_cursor(self,cursor_style: CursorStyle,size: Optional[int] = None) -> None:
        cursor = self.create_custom_cursor(cursor_style, size)
        QApplication.setOverrideCursor(cursor)

    def restore_global_cursor(self) -> None:
        # 恢复应用程序默认全局光标
        QApplication.restoreOverrideCursor()

    def clear_cache(self, specific_style: Optional[CursorStyle] = None) -> None:
        if specific_style is None:
            self._cursor_cache.clear()
        else:
            keys_to_remove = [
                key for key in self._cursor_cache.keys()
                if key[0] == specific_style
            ]
            for key in keys_to_remove:
                del self._cursor_cache[key]


    def update_default_size(self, new_size: int) -> None:

        if not isinstance(new_size, int) or new_size <= 0:
            raise ValueError("Default size must be a positive integer")
        self._default_size = new_size


class Cursor:
    _instance: Optional[CursorManager] = None

    @classmethod
    def get_instance(cls, default_size: int = 24) -> CursorManager:
        if cls._instance is None:
            cls._instance = CursorManager(default_size)
        return cls._instance


cursor = Cursor.get_instance()