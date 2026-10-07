"""环境：变量绑定表 + 指向外层环境的指针（词法作用域的关键）。

查找沿外层链一路向上；define 只写入**当前**这一层。
"""


from errors import SchemeError


class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def define(self, name, value):
        """在当前环境绑定一个名字。"""
        self.bindings[name] = value

    def lookup(self, name):
        """沿外层链查找名字；找不到时报未绑定错误。"""
        env = self
        while env is not None:
            if name in env.bindings:
                return env.bindings[name]
            env = env.parent
        raise SchemeError(f"未绑定的变量: {name}")
