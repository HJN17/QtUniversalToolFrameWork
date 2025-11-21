# coding: utf-8
# 导入functools模块中的singledispatch（单分派装饰器）和update_wrapper（更新包装器元数据）函数
from functools import singledispatch, update_wrapper


# 定义一个单分派泛型方法描述符类，用于实现基于第一个参数类型的方法重载
class singledispatchmethod:
    """
    
    单分派泛型方法描述符类
    
    作用：实现基于第一个参数类型的函数重载机制，支持包装现有描述符，
          并能将非描述符类型的可调用对象作为实例方法处理。
          （单分派：指仅根据第一个参数的类型来选择对应的重载实现）
    """

    # 定义构造方法，初始化泛型方法
    def __init__(self, func):
        # 条件判断：检查传入的func是否为可调用对象（callable）或具有__get__属性的描述符
        if not callable(func) and not hasattr(func, "__get__"):
            # 若不满足条件，抛出TypeError异常，提示func不是可调用对象或描述符
            raise TypeError(f"{func!r} is not callable or a descriptor")
        
        # 初始化单分派调度器：使用singledispatch装饰器包装func，创建调度器实例
        self.dispatcher = singledispatch(func)
        # 将原始函数保存到实例属性，用于后续元数据复制和方法绑定
        self.func = func

    # 定义注册方法，用于为特定类型注册重载实现
    def register(self, cls, method=None):
        """
        注册泛型方法的重载实现
        
        参数：
            cls (type): 要为其注册重载方法的类型
            method (callable, optional): 对应cls类型的重载实现方法，若为None则返回装饰器
        
        返回：
            callable: 若method不为None则返回method，否则返回一个装饰器函数，用于后续注册
        
        说明：该方法委托给dispatcher的register方法，实现类型与重载方法的绑定
        """
        # 调用调度器的register方法，注册类型cls和对应的实现方法method
        return self.dispatcher.register(cls, func=method)

    # 实现描述符协议的__get__方法，用于在访问属性时返回绑定后的方法
    def __get__(self, obj, cls=None):
        # 定义内部包装方法，用于处理参数分发和方法调用
        def _method(*args, **kwargs):
            # 条件判断：检查是否存在位置参数（args不为空）
            if args:
                # 根据第一个位置参数的类型（args[0].__class__）获取对应的重载方法
                method = self.dispatcher.dispatch(args[0].__class__)
            else:
                # 若没有位置参数，默认使用原始函数
                method = self.func
                # 遍历关键字参数的值，查找在调度器注册表中存在的类型
                for v in kwargs.values():
                    if v.__class__ in self.dispatcher.registry:
                        # 找到匹配类型，获取对应的重载方法
                        method = self.dispatcher.dispatch(v.__class__)
                        # 若找到的方法不是原始函数，则跳出循环
                        if method is not self.func:
                            break

            # 调用方法的__get__方法绑定实例（obj）或类（cls），并传入参数执行
            return method.__get__(obj, cls)(*args, **kwargs)

        # 设置包装方法的抽象方法标志，继承原始函数的__isabstractmethod__属性
        _method.__isabstractmethod__ = self.__isabstractmethod__
        # 为包装方法添加register属性，指向当前类的register方法，支持链式注册
        _method.register = self.register
        # 更新包装方法的元数据（如名称、文档字符串等），使其与原始函数一致
        update_wrapper(_method, self.func)
        # 返回包装后的方法
        return _method

    # 使用@property装饰器，将__isabstractmethod__方法转换为属性
    @property
    def __isabstractmethod__(self):
        """
        获取原始函数的抽象方法标志
        
        返回：
            bool: 若原始函数（self.func）具有__isabstractmethod__属性且为True，则返回True；否则返回False
        
        说明：用于支持抽象基类（ABC），标识该方法是否为抽象方法
        """
        # 获取原始函数的__isabstractmethod__属性，若不存在则返回False
        return getattr(self.func, '__isabstractmethod__', False)
