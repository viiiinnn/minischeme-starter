"""内置过程库（spec §5）与全局初始环境。

每个内置过程接收**已求值**的参数列表，返回一个 Scheme 值
（display/newline 返回 None，表示“无值、不打印结果行”）。
"""

import sys

from environment import Environment
from errors import SchemeError
from printer import display_string
from values import (
    NIL,
    Builtin,
    NilType,
    Pair,
    Procedure,
    Str,
    Symbol,
    is_number,
    is_text,
)


def _check_number(name, value):
    if not is_number(value):
        raise SchemeError(f"{name}: 需要数字参数, 得到 {display_string(value)}")
    return value


def _check_arity(name, args, count):
    if len(args) != count:
        raise SchemeError(f"{name}: 需要 {count} 个参数, 得到 {len(args)}")


def _check_int(name, value):
    if type(value) is not int:
        raise SchemeError(f"{name}: 需要整数参数, 得到 {display_string(value)}")
    return value


def _trunc_div(a, b):
    """向零截断的整数除法（Scheme 的 quotient 语义）。"""
    if b == 0:
        raise SchemeError("/: 除数不能为 0")
    quotient = abs(a) // abs(b)
    return quotient if (a < 0) == (b < 0) else -quotient


def _add(args):
    total = 0
    for a in args:
        total += _check_number("+", a)
    return total


def _sub(args):
    if not args:
        raise SchemeError("-: 参数个数不足")
    if len(args) == 1:
        return -_check_number("-", args[0])
    result = _check_number("-", args[0])
    for a in args[1:]:
        result -= _check_number("-", a)
    return result


def _mul(args):
    total = 1
    for a in args:
        total *= _check_number("*", a)
    return total


def _div(args):
    if not args:
        raise SchemeError("/: 参数个数不足")
    if len(args) == 1:  # 单参数求倒数（浮点）
        value = _check_number("/", args[0])
        if value == 0:
            raise SchemeError("/: 除数不能为 0")
        return 1 / float(value)
    result = _check_number("/", args[0])
    for a in args[1:]:
        a = _check_number("/", a)
        if type(result) is int and type(a) is int:
            result = _trunc_div(result, a)
        else:
            if a == 0:
                raise SchemeError("/: 除数不能为 0")
            result = result / a
    return result


def _modulo(args):
    if len(args) != 2:
        raise SchemeError("modulo: 需要 2 个参数")
    a, b = _check_int("modulo", args[0]), _check_int("modulo", args[1])
    if b == 0:
        raise SchemeError("modulo: 除数不能为 0")
    return a % b  # Python 的 % 与 Scheme modulo 同为“结果符号随除数”


def _quotient(args):
    if len(args) != 2:
        raise SchemeError("quotient: 需要 2 个参数")
    return _trunc_div(_check_int("quotient", args[0]), _check_int("quotient", args[1]))


def _expt(args):
    if len(args) != 2:
        raise SchemeError("expt: 需要 2 个参数")
    base, power = _check_number("expt", args[0]), _check_number("expt", args[1])
    try:
        return base ** power
    except (OverflowError, ZeroDivisionError) as exc:
        raise SchemeError(f"expt: {exc}") from None


def _abs(args):
    if len(args) != 1:
        raise SchemeError("abs: 需要 1 个参数")
    return abs(_check_number("abs", args[0]))


def _numeric_compare(op, name, a, b):
    """相邻两项比较：数字按数值，符号/字符串按字典序，其余报错。"""
    if is_number(a) and is_number(b):
        return op(a, b)
    if is_text(a) and is_text(b):
        return op(str(a), str(b))
    raise SchemeError(f"{name}: 无法比较 {display_string(a)} 与 {display_string(b)}")


def _make_compare(name, op):
    def compare(args):
        # 链式比较：相邻两两都成立才为真；少于两个参数视为真
        for a, b in zip(args, args[1:]):
            if not _numeric_compare(op, name, a, b):
                return False
        return True

    return compare


def _not(args):
    if len(args) != 1:
        raise SchemeError("not: 需要 1 个参数")
    return args[0] is False


def _cons(args):
    if len(args) != 2:
        raise SchemeError("cons: 需要 2 个参数")
    return Pair(args[0], args[1])


def _car(args):
    _check_arity("car", args, 1)
    if not isinstance(args[0], Pair):
        raise SchemeError(f"car: 需要点对, 得到 {display_string(args[0])}")
    return args[0].car


def _cdr(args):
    _check_arity("cdr", args, 1)
    if not isinstance(args[0], Pair):
        raise SchemeError(f"cdr: 需要点对, 得到 {display_string(args[0])}")
    return args[0].cdr


def _list(args):
    result = NIL
    for a in reversed(args):
        result = Pair(a, result)
    return result


def _length(args):
    if len(args) != 1:
        raise SchemeError("length: 需要 1 个参数")
    count = 0
    node = args[0]
    while isinstance(node, Pair):
        count += 1
        node = node.cdr
    if not isinstance(node, NilType):
        raise SchemeError("length: 参数不是真列表")
    return count


def _list_items(value, name):
    """把真列表展开成 Python 列表；不是真列表则报错。"""
    items = []
    node = value
    while isinstance(node, Pair):
        items.append(node.car)
        node = node.cdr
    if not isinstance(node, NilType):
        raise SchemeError(f"{name}: 参数不是真列表")
    return items


def _append(args):
    if not args:
        return NIL
    result = args[-1]
    for arg in reversed(args[:-1]):
        for item in reversed(_list_items(arg, "append")):
            result = Pair(item, result)
    return result


def _nullp(args):
    _check_arity("null?", args, 1)
    return isinstance(args[0], NilType)


def _pairp(args):
    _check_arity("pair?", args, 1)
    return isinstance(args[0], Pair)


def _listp(args):
    _check_arity("list?", args, 1)
    node = args[0]
    while isinstance(node, Pair):
        node = node.cdr
    return isinstance(node, NilType)


def _make_type_predicate(name, predicate):
    def check(args):
        if len(args) != 1:
            raise SchemeError(f"{name}: 需要 1 个参数")
        return predicate(args[0])

    return check


def _zero(args):
    _check_arity("zero?", args, 1)
    return _check_number("zero?", args[0]) == 0


def _even(args):
    _check_arity("even?", args, 1)
    return _check_int("even?", args[0]) % 2 == 0


def _odd(args):
    _check_arity("odd?", args, 1)
    return _check_int("odd?", args[0]) % 2 != 0


def _eq(args):
    if len(args) != 2:
        raise SchemeError("eq?: 需要 2 个参数")
    a, b = args
    if isinstance(a, Pair) or isinstance(b, Pair):
        return a is b  # 复合数据比同一性
    if type(a) is not type(b):
        return False
    return a is b or a == b


def _equal(args):
    if len(args) != 2:
        raise SchemeError("equal?: 需要 2 个参数")
    a, b = args
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _equal([a.car, b.car]) and _equal([a.cdr, b.cdr])
    if is_number(a) and is_number(b):
        return a == b
    if type(a) is not type(b):  # 避免 True == 1、'a' == "a" 之类的误判
        return False
    return a is b or a == b


def _display(args):
    if len(args) != 1:
        raise SchemeError("display: 需要 1 个参数")
    sys.stdout.write(display_string(args[0]))
    return None  # 无值，顶层不打印结果行


def _newline(args):
    if args:
        raise SchemeError("newline: 不接受参数")
    sys.stdout.write("\n")
    return None


def _is_procedure(value):
    return isinstance(value, (Builtin, Procedure))


#: 全部内置过程：名字 -> 实现函数（参数为已求值的实参列表）
_TABLE = [
    ("+", _add),
    ("-", _sub),
    ("*", _mul),
    ("/", _div),
    ("modulo", _modulo),
    ("quotient", _quotient),
    ("expt", _expt),
    ("abs", _abs),
    ("=", _make_compare("=", lambda a, b: a == b)),
    ("<", _make_compare("<", lambda a, b: a < b)),
    (">", _make_compare(">", lambda a, b: a > b)),
    ("<=", _make_compare("<=", lambda a, b: a <= b)),
    (">=", _make_compare(">=", lambda a, b: a >= b)),
    ("not", _not),
    ("cons", _cons),
    ("car", _car),
    ("cdr", _cdr),
    ("list", _list),
    ("length", _length),
    ("append", _append),
    ("null?", _nullp),
    ("pair?", _pairp),
    ("list?", _listp),
    ("number?", _make_type_predicate("number?", is_number)),
    ("boolean?", _make_type_predicate("boolean?", lambda v: type(v) is bool)),
    ("symbol?", _make_type_predicate("symbol?", lambda v: isinstance(v, Symbol))),
    ("string?", _make_type_predicate("string?", lambda v: isinstance(v, Str))),
    ("procedure?", _make_type_predicate("procedure?", _is_procedure)),
    ("zero?", _zero),
    ("even?", _even),
    ("odd?", _odd),
    ("eq?", _eq),
    ("equal?", _equal),
    ("display", _display),
    ("newline", _newline),
]


def make_global_env():
    """构造只含内置过程的初始全局环境。"""
    env = Environment()
    for name, fn in _TABLE:
        env.define(Symbol(name), Builtin(name, fn))
    return env
