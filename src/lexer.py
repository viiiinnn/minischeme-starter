"""词法分析：程序文本 -> Token 列表。

只负责把字符切成“零件”：括号、引号、字符串、数字、布尔、符号，
并顺手丢掉注释。语法结构（嵌套）交给 syntax.py。
"""

import re

from errors import SchemeError
from values import Symbol, Str

#: 一个原子（token 文本）到哪里结束
_DELIMS = set(' \t\r\n();\'"')
#: 整数：可选正负号 + 纯数字
_INT_RE = re.compile(r"^[+-]?[0-9]+$")
#: 浮点：整数部分/小数部分至少出现一个，可带指数
_FLOAT_RE = re.compile(r"^[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?$")
#: 字符串转义
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


class Token:
    """kind: '(' ')' '.' "'" 'string' 'bool' 'int' 'float' 'symbol'"""

    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.kind!r}, {self.value!r}, line={self.line})"


def _atom_token(text, line):
    """把一段裸文本归类为点记号 / 布尔 / 整数 / 浮点 / 符号。"""
    if text == ".":
        # 点对里的 "." 是独立记号，必须单独成 token，否则 (a . b) 会被读成三个符号
        return Token(".", Symbol("."), line)
    if text == "#t":
        return Token("bool", True, line)
    if text == "#f":
        return Token("bool", False, line)
    if _INT_RE.match(text):
        return Token("int", int(text), line)
    if _FLOAT_RE.match(text):
        return Token("float", float(text), line)
    return Token("symbol", Symbol(text), line)


def tokenize(source):
    """把程序文本切成 Token 列表；发现非法字符时抛 SchemeError。"""
    tokens = []
    i = 0
    line = 1
    n = len(source)

    while i < n:
        ch = source[i]

        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch in " \t\r\ufeff":  # 含 BOM：可能出现在文件开头或中间
            i += 1
            continue
        if ch == ";":  # 注释到行尾
            while i < n and source[i] != "\n":
                i += 1
            continue
        if ch in "()'":
            tokens.append(Token(ch, ch, line))
            i += 1
            continue

        if ch == '"':
            start_line = line
            i += 1
            buf = []
            closed = False
            while i < n:
                c = source[i]
                if c == '"':
                    closed = True
                    i += 1
                    break
                if c == "\\":
                    if i + 1 >= n:
                        break
                    esc = source[i + 1]
                    if esc not in _ESCAPES:
                        raise SchemeError(f"非法转义字符 \\{esc}", line)
                    buf.append(_ESCAPES[esc])
                    i += 2
                    continue
                if c == "\n":
                    line += 1
                buf.append(c)
                i += 1
            if not closed:
                raise SchemeError("字符串没有闭合的双引号", start_line)
            tokens.append(Token("string", Str("".join(buf)), start_line))
            continue

        # 裸原子：读到空白或分隔字符为止
        start = i
        start_line = line
        while i < n and source[i] not in _DELIMS:
            i += 1
        tokens.append(_atom_token(source[start:i], start_line))

    return tokens
