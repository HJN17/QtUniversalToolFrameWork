import os

from PyQt5.QtCore import Qt,pyqtSlot
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,QFileDialog,QHBoxLayout)
from PyQt5.QtGui import QPixmap,QColor

from common.style_sheet import StyleSheet
from common.image_utils import get_image_paths,ImageManager

from components.widgets.gallery_interface import TitleToolBar
from components.widgets.image_canva import ImageCanvas,ImageProgressWidget,ImageSearchFlyoutView

from components.widgets import InfoBar, InfoBarPosition, Flyout, FlyoutAnimationType,CommandBarLabel,CommandBar
from common.icon import FluentIcon as FIF,Action

class ImageViewInterface(QWidget):
    """ 图片视图接口类：继承自QWidget，用于显示图片和操作图片 """


    INSTRUCTION = ("用于展示图片、旋转、浏览（上一张/下一张）、缩放、删除、搜索等功能")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('ImageViewInterface')
        
        self._imageManager = ImageManager(self)
        self._titleToolBar = TitleToolBar(":/resource/images/image.svg", '图像工具',self.INSTRUCTION,self) #FIF.PHOTO
        self._progressWidget = ImageProgressWidget(self)
        self._image_canvas = ImageCanvas(self)
        self._image_name_label = CommandBarLabel(self)
        self._commandBar = self.createCommandBar()

        self._current_dir = ""
        
        self._progressWidget.progress.connect(self._on_progress_changed)
        self._imageManager.image_loaded.connect(self._display_current_image)
        self._imageManager.current_item_changed.connect(self._set_progress_value)
        self._imageManager.item_deleted.connect(self._set_progress_range)
        self._imageManager.item_inserted.connect(self._set_progress_range)
        self._imageManager.model_reset.connect(self._set_progress_range)
    
        self._init_ui()
        
    def _init_ui(self):

        StyleSheet.GALLERY_INTERFACE.apply(self)
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setContentsMargins(10, 10, 10, 10)
        vBoxLayout.setSpacing(2)
        vBoxLayout.setAlignment(Qt.AlignTop) 

        vBoxLayout.addWidget(self._titleToolBar,0,Qt.AlignLeft)
        vBoxLayout.addWidget(self._commandBar,0,Qt.AlignHCenter)
        vBoxLayout.setSpacing(10)
        vBoxLayout.addWidget(self._image_canvas,1)


        self._image_name_label.setContentsMargins(20, 0, 0, 0)
        self._image_name_label.setWordWrap(False)
        self._image_name_label.setTextColor(QColor(98, 98, 98), QColor(228, 228, 228))
        vBoxLayout.addWidget(self._image_name_label,0,Qt.AlignLeft)

    def createCommandBar(self):
            bar = CommandBar(self)
            bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

            bar.addActions([
                Action(FIF.ADD, "加载", triggered=self._on_folder_path_changed),
                Action(FIF.EDIT, "编辑", checkable=True),
            ])

            bar.addSeparator()
            
            bar.addActions([
                Action(FIF.LEFT_ARROW,triggered=self._imageManager.previous,shortcut="Left"),
                Action(FIF.RIGHT_ARROW,triggered=self._imageManager.next,shortcut="Right"),
            ])

            bar.addWidget(self._progressWidget)

            bar.addActions([
                Action(FIF.SEARCH,triggered=self._on_search_clicked),
            ])

            bar.addSeparator()

            bar.addActions([
                Action(FIF.ROTATE,triggered=self._image_canvas.rotate_image,shortcut="R"),
                Action(FIF.ZOOM_IN,triggered=self._image_canvas.zoom_in),
                Action(FIF.ZOOM_OUT,triggered=self._image_canvas.zoom_out),
                Action(FIF.DELETE,triggered=self._on_delete_image_clicked,shortcut="Delete"),
            ])
            return bar
    

    def _set_progress_range(self):
        self._progressWidget.setRange(1, self._imageManager.count)

    def _set_progress_value(self):
        self._progressWidget.setProgress(self._imageManager.current_index+1)

    def _on_folder_path_changed(self,):

        folder = QFileDialog.getExistingDirectory(
            self, "选择图像文件夹", self._current_dir or "./",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            self._current_dir = folder
            image_paths = get_image_paths(self._current_dir)
            self._imageManager.set_items(image_paths)

    @pyqtSlot(QPixmap)
    def _display_current_image(self, pixmap: QPixmap):
        if not pixmap:
            return

        self._image_canvas.load_pixmap(pixmap)
        self._image_name_label.setText(self._imageManager.current_item)

    @pyqtSlot(int)
    def _on_progress_changed(self, value: int):
        self._imageManager.go_to(value-1)
    

    def _on_search_clicked(self):

        if not self._imageManager.items:
            return

        searchFlyoutView = ImageSearchFlyoutView()
        searchFlyoutView.searchSignal.connect(self._on_search_signal)
        searchFlyoutView.set_stands([os.path.basename(p) for p in self._imageManager.items])
        Flyout.make(view = searchFlyoutView,
                    target = self._commandBar,
                    parent = self,
                    aniType = FlyoutAnimationType.DROP_DOWN)
        

    @pyqtSlot(str)
    def _on_search_signal(self, search_text: str):
        if search_text:
            try:
                image_index = self._imageManager.items.index(os.path.join(self._current_dir, search_text))    
            except ValueError:
                self._show_error_message("搜索失败", f"未找到图像 {search_text}")
                return
            
            self._imageManager.go_to(image_index)

        
    
    def _on_delete_image_clicked(self):
        if not self._imageManager.items or self._imageManager.current_index == -1:
            return

        current_path = self._imageManager.current_item
        current_filename = os.path.basename(current_path)
        self._imageManager.delete_current()
        try:
            os.remove(current_path)

            self._show_info_message("删除成功", f"图像文件 {current_filename} 已成功删除")
        except Exception as e:
            self._show_error_message("删除失败", f"无法删除图片 {current_filename}：{str(e)}")
            return
        
        
        
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._commandBar:
            self._commandBar.setFixedWidth(min(self._commandBar.suitableWidth(), self.width()-20))
            self._commandBar.updateGeometry()

  
    def _show_info_message(self, title: str, content: str):
        InfoBar.info(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, position=InfoBarPosition.TOP_RIGHT,
            duration=2000, parent=self
        )

    def _show_error_message(self, title: str, content: str):
        InfoBar.error(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, position=InfoBarPosition.TOP_RIGHT,
            duration=3000, parent=self
        )

