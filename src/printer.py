"""打印：Scheme 值 -> 文本。

- ``to_string`` 用于打印求值结果（字符串带引号、内部转义）
- ``display_string`` 用于 display 内置过程（字符串不带引号、原样输出）
"""

from values import NilType, Pair, Symbol, Str, Builtin, Procedure


def _quote(text):
    """把字符串内容转义成带双引号的字面量写法。"""
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def to_string(value):
    """把值转成 spec §8 规定的打印形式。"""
    if value is None:
        return ""
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, Str):
        return _quote(str(value))
    if isinstance(value, (int, float)):
        return repr(value) if isinstance(value, float) else str(value)
    if isinstance(value, NilType):
        return "()"
    if isinstance(value, Pair):
        parts = []
        node = value
        while isinstance(node, Pair):
            parts.append(to_string(node.car))
            node = node.cdr
        if isinstance(node, NilType):
            return "(" + " ".join(parts) + ")"
        # 非真列表：最后一个元素后跟 " . 剩余"
        return "(" + " ".join(parts) + " . " + to_string(node) + ")"
    if isinstance(value, (Builtin, Procedure)):
        return "#<procedure>"
    return str(value)


def display_string(value):
    """display 的输出：字符串不带引号、不转义；其余与 to_string 相同。"""
    if isinstance(value, Str):
        return str(value)
    return to_string(value)
