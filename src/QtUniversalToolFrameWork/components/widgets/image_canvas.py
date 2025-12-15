# coding=utf-8
from PyQt5.QtWidgets import QLabel,QFrame,QWidget,QHBoxLayout,QVBoxLayout,QCompleter
from PyQt5.QtGui import QPainter, QPixmap, QTransform,QFont,QColor,QPainterPath
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF,QTimer,QRectF,QSize

from PyQt5.QtCore import pyqtSignal

from ...common.font import getFont

from .line_edit import SearchLineEdit,NumberEdit
from .flyout import FlyoutViewBase
from .slider import Slider

class ScaleLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 26)
        self.hide_scale()
        self.setAlignment(Qt.AlignCenter)
        self._scale = 1
    
    def show_scale(self, scale):
        """ 显示缩放比例标签 """
        self._scale = int(scale*100)
        # 判断是否可见
        if not self.isVisible():
            self.show()
            QTimer.singleShot(2000, self.hide_scale)
        

    def paintEvent(self, e):
        """ 绘制事件处理 """
        painter = QPainter(self)

        painter.setRenderHints(
            QPainter.TextAntialiasing |
            QPainter.HighQualityAntialiasing |
            QPainter.SmoothPixmapTransform 
        )
        
        rectf = QRectF(self.rect()) 
        rounded_rect = QPainterPath() # 创建圆角矩形路径
        rounded_rect.addRoundedRect(rectf, 13, 13)

        painter.setBrush(QColor(0, 0, 0, 90))
        painter.setPen(Qt.NoPen)
        painter.drawPath(rounded_rect)

        
        painter.setPen(QColor(255, 255, 255))

        rectf.adjust(5,1,-1,-1)

        painter.setFont(getFont(12, QFont.ExtraBold))

        painter.drawText(rectf, Qt.AlignCenter, f"{self._scale}%")

    def hide_scale(self):
        """ 隐藏缩放比例标签 """
        self.hide()
    
    def move_scale_label(self):
        """ 移动缩放比例标签到指定位置 """
        parent_width = self.parent().width()
        parent_height = self.parent().height()
        x = (parent_width - self.width()) // 2
        y = (parent_height - self.height()) // 2
        self.move(x, y)

class ImageSearchFlyoutView(FlyoutViewBase):
    """ 图片搜索浮窗视图 """

    searchSignal = pyqtSignal(str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)

        self._stands = [] # 图片名称列表
        
        self._searchLineEdit = SearchLineEdit(self)
        self._searchLineEdit.hBoxLayout.setContentsMargins(0, 0, 12, 0)
        self._searchLineEdit.searchSignal.connect(self.searchSignal)
        self._init_ui()
        self.set_stands(self._stands)

    def _init_ui(self):
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(10)

        self._searchLineEdit.setPlaceholderText("请输入图片名称")
        self._searchLineEdit.setFixedWidth(600)
        self._searchLineEdit.setFixedHeight(40)
        self._searchLineEdit.setSearchButtonSize(24)
        self._searchLineEdit.setClearButtonSize(16)

        vBoxLayout.addWidget(self._searchLineEdit,0,Qt.AlignCenter)
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(10)
        self.setFixedSize(660, 80)

    def set_stands(self, stands: list):
        self._stands = stands
        completer = QCompleter(self._stands)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        self._searchLineEdit.setCompleter(completer)

    def closeEvent(self, e):
        """ 关闭事件处理 """
        super().closeEvent(e)

    def keyPressEvent(self, e):
        """ 键盘事件处理 """
        if e.key() == Qt.Key_Escape:
            self.close()
            return
        if e.key() == Qt.Key_Return: # 按下回车键时触发搜索
            self.searchSignal.emit(self._searchLineEdit.text())
            return

    def showEvent(self, e):
        """ 显示事件处理 """
        super().showEvent(e)
        self._searchLineEdit.setFocus()

class ImageProgressWidget(QWidget):
    
    progress = pyqtSignal(int)

    def __init__(self,parent=None):
        super().__init__(parent=parent)

        self.slider = Slider(Qt.Horizontal)
        self.numberEdit = NumberEdit(self)
        
        self.numberEdit.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.numberEdit.setValue)
        self.slider.valueChanged.connect(self.progress) 
        self._init_ui()
        self.set_slider_range(0, 0)
        

    def _init_ui(self):
        hBoxLayout = QHBoxLayout(self)
        hBoxLayout.setContentsMargins(0, 0, 0, 0)
        hBoxLayout.addSpacing(4)

        self.slider.setMinimumWidth(250)
        self.slider.setFixedHeight(13)

        self.numberEdit.setFixedWidth(45)
        self.numberEdit.setFixedHeight(26)

        hBoxLayout.addWidget(self.slider)
        hBoxLayout.addWidget(self.numberEdit)

    def set_slider_width(self, value: int):
        self.slider.setMinimumWidth(value)

    def set_slider_value(self, value: int):
       self.slider.setValue(value)
    
    def set_slider_range(self, min: int, max: int):
        self.slider.setRange(min, max)
        self.numberEdit.setRange(min, max)

class ImageCanvas(QFrame):

    MIN_SCALE = 0.1
    MAX_SCALE = 9.0
    ZOOM_IN_FACTOR = 1.2 
    ZOOM_OUT_FACTOR = 0.8 
    WHEEL_ZOOM_FACTOR = 1.2 
    ROTATE_ANGLE = 90
    RESIZE_THRESHOLD = 5 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.original_pixmap  = None
        self._scaled_pixmap = None 

        self.scale = 1.0 

        self.offset = QPoint(0, 0)
        self.dragging = False 
        self.last_pos = QPoint()
        self.last_canvas_size = self.size()

        self.original_w_h = None
        self.total_rotate_angle = 0


        self.setFocusPolicy(Qt.StrongFocus)
        self._scale_label  = ScaleLabel(self)


    def load_pixmap(self, pixmap: QPixmap):

        self.original_pixmap = pixmap if not pixmap.isNull() else None
        self._scaled_pixmap = None

        if self.original_pixmap:

            self.original_w_h = QSize(self.original_pixmap.width(), self.original_pixmap.height())

            self.init_load_image()    
            self.update_scaled_image()

        self.update()

    def load_image(self, image_path: str):
        pixmap = QPixmap(image_path)
        self.load_pixmap(pixmap)


    def init_load_image(self):
        """初始化图像加载：计算初始缩放比例和居中偏移"""
        if not self.original_pixmap or self.width() <= 0 or self.height() <= 0:
            self.scale = 1.0
            self.offset = QPoint(0, 0)
            return
        
        canvas_w, canvas_h = self.width(), self.height()
        img_w, img_h = self.original_pixmap.width(), self.original_pixmap.height()
        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h
        self.scale = min(scale_w, scale_h)

        scaled_w = int(img_w * self.scale)
        scaled_h = int(img_h * self.scale)

        self.offset = QPoint(
            (canvas_w - scaled_w) // 2,
            (canvas_h - scaled_h) // 2
        )

    def update_scaled_image(self):

        if not self.original_pixmap:
            self._scaled_pixmap = None
            return
        
        img_w, img_h = self.original_pixmap.width(), self.original_pixmap.height()
        scaled_w = int(img_w * self.scale)
        scaled_h = int(img_h * self.scale)
   
        if scaled_w <= 0 or scaled_h <= 0:
            self._scaled_pixmap = None
            return

        self._scaled_pixmap = self.original_pixmap.scaled(
            scaled_w, scaled_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

    def _update_zoom_offset(self, scale_factor: float, center_pos: QPoint):
        if not self.original_pixmap:
            return

       
        old_scale = self.scale

        self.scale *= scale_factor
        self.scale = max(self.MIN_SCALE, min(self.scale, self.MAX_SCALE))

        # 计算缩放中心点在「原始图像坐标系」中的位置（关键：坐标转换）
        img_x = (center_pos.x() - self.offset.x()) / old_scale
        img_y = (center_pos.y() - self.offset.y()) / old_scale

      
        new_offset_x = int(center_pos.x() - img_x * self.scale)
        new_offset_y = int(center_pos.y() - img_y * self.scale)
        self.offset = QPoint(new_offset_x, new_offset_y)

        self.update_scaled_image()
        self.update()
        self._scale_label.show_scale(self.scale)


    def zoom_to(self, scale_factor: float):
        if not self.original_pixmap:
            return
        center_pos = self.rect().center() # 缩放中心点：画布中心
        self._update_zoom_offset(scale_factor, center_pos)


    def zoom_in(self):
        self.zoom_to(self.ZOOM_IN_FACTOR)

    def zoom_out(self):
        self.zoom_to(self.ZOOM_OUT_FACTOR)
    
    def rotate_image(self):

        if not self.original_pixmap:
            return

        transform = QTransform().rotate(self.ROTATE_ANGLE)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        self.total_rotate_angle += self.ROTATE_ANGLE
        self.total_rotate_angle %= 360  # 角度归一化（0-359）


        self.init_load_image()
        self.update_scaled_image()
        self.update()


    def mousePressEvent(self, event):
        """
        处理鼠标按下事件。

        :param event: 鼠标事件对象。
        """
        if event.button() == Qt.RightButton:
            self.dragging = True
            self.last_pos = event.pos() 
            self.setCursor(Qt.ClosedHandCursor) # 切换为拖动游标
            return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        """
        处理鼠标移动事件。

        :param event: 鼠标事件对象。
        """
        if self.dragging and self.original_pixmap  is not None:
            delta = event.pos() - self.last_pos 
            self.offset += delta  # 更新图像显示的偏移量
            self.last_pos = event.pos()  # 记录当前鼠标位置
            self.update()
            return
    
    
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        处理鼠标释放事件。

        :param event: 鼠标事件对象。
        """
        if event.button() == Qt.RightButton and self.dragging :
            self.dragging = False 
            self.setCursor(Qt.ArrowCursor)
            return
           
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """处理鼠标滚轮事件：以鼠标位置为中心缩放"""
        if not self.original_pixmap:
            super().wheelEvent(event)
            return

        scale_factor = self.WHEEL_ZOOM_FACTOR if event.angleDelta().y() > 0 else 1 / self.WHEEL_ZOOM_FACTOR
        mouse_pos = event.pos()
        self._update_zoom_offset(scale_factor, mouse_pos)

        event.accept()



    def resizeEvent(self, event):
        current_size = self.size()
        width_diff = abs(current_size.width() - self.last_canvas_size.width())
        height_diff = abs(current_size.height() - self.last_canvas_size.height())
    
        if width_diff < self.RESIZE_THRESHOLD and height_diff < self.RESIZE_THRESHOLD:
            super().resizeEvent(event)
            return

        self._scale_label.move_scale_label()
        if self.original_pixmap:
            self.init_load_image()
            self.update_scaled_image()
            self.update()

        self.last_canvas_size = current_size
        super().resizeEvent(event)
    
 