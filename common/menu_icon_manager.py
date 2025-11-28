# coding:utf-8
from PyQt5.QtCore import Qt, QObject

class MenuFunctionButtonManager(QObject):
    _instance = None 
    _initialized = False # 是否初始化

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not MenuFunctionButtonManager._initialized:
            super().__init__()
            MenuFunctionButtonManager._initialized = True

            self._menuFunctionButtonItems = {}

    def __str__(self):
        return f"MenuFunctionButtonManager({self._menuFunctionButtonItems})"

    def remove_menu_function_button_item(self, ui_id : str, icon_item):

        if ui_id in self._menuFunctionButtonItems:
            self._menuFunctionButtonItems[ui_id].remove(icon_item)

    def set_menu_function_button_item(self, ui_id : str, icon_item):

        if ui_id in self._menuFunctionButtonItems:
            self._menuFunctionButtonItems[ui_id].append(icon_item)
        else:
            self._menuFunctionButtonItems[ui_id] = [icon_item]

    def get_menu_function_button_items(self, ui_id : str):
        return self._menuFunctionButtonItems.get(ui_id, [])


mfb = MenuFunctionButtonManager()