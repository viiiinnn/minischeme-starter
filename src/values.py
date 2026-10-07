"""mini-Scheme 的值表示。

解释器里的每个 Scheme 值都对应一个 Python 对象：

- 整数/浮点/布尔 -> Python 的 int / float / bool
- 符号            -> Symbol（str 的子类）
- 字符串          -> Str（同样是 str 的子类，但与 Symbol 类型不同）
- 空表 ()         -> 单例 NIL
- 点对            -> Pair（car 指向第一项，cdr 指向下一段）
- 过程            -> Builtin（内置）/ Procedure（lambda 闭包）

注意：Symbol 与 Str 必须是两个不同的类型，否则 ``(equal? 'a "a")``
会因为 Python 的字符串相等而误判为真。
"""


class Symbol(str):
    """Scheme 符号，如 ``foo``、``+``。"""

    __slots__ = ()

    def __repr__(self):
        return str.__repr__(str(self))  # 报错信息里显示成 'foo' 而不是 Symbol('foo')


class Str(str):
    """Scheme 字符串，如 ``"hello"``。"""

    __slots__ = ()

    def __repr__(self):
        return str.__repr__(str(self))


class NilType:
    """空表 ``()`` 的单例类型。"""

    __slots__ = ()

    def __repr__(self):
        return "()"


#: 空表。全程序只有一个实例，因此 ``(eq? '() '())`` 为真。
NIL = NilType()


class Pair:
    """点对：列表 ``'(1 2 3)`` 即 ``(1 . (2 . (3 . ())))``。"""

    __slots__ = ("car", "cdr")

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr


class Builtin:
    """内置过程（spec §5），由 Python 函数实现。"""

    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


class Procedure:
    """lambda 产生的闭包：记住参数、函数体与**定义时**的环境。"""

    __slots__ = ("params", "body", "env")

    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env


def is_number(value):
    """是否为数字。

    必须用 ``type`` 判断：Python 里 ``bool`` 是 ``int`` 的子类，
    ``isinstance(True, int)`` 为真，会让 ``(number? #t)`` 误判。
    """
    return type(value) in (int, float)


def is_text(value):
    """是否为符号或字符串（两者可按字典序比较）。"""
    return isinstance(value, (Symbol, Str))


def is_truthy(value):
    """mini-Scheme 只有 ``#f`` 为假，0、()、\"\" 均为真。"""
    return value is not False


def datumize(expr):
    """把语法树中的 Python 列表转换成点对链（quote 用）。

    解析器用 Python list 表示成对括号，而 quote 需要把数据原样交出，
    数据的表示必须与 ``cons`` 构造出来的点对一致。
    """
    if isinstance(expr, list):
        result = NIL
        for item in reversed(expr):
            result = Pair(datumize(item), result)
        return result
    if isinstance(expr, Pair):
        return Pair(datumize(expr.car), datumize(expr.cdr))
    return expr
