"""语法分析：Token 列表 -> 表达式（嵌套数据结构）。

表达式的 Python 表示：
- 括号表达式   -> Python list，例如 ``(+ 1 2)`` 变成 ``[Symbol('+'), 1, 2]``
- 引用简写     -> ``[Symbol('quote'), 数据]``
- 基本值       -> int / float / bool / Str / Symbol
- 点对字面量   -> Pair（只出现在 ``(1 . 2)`` 这种带点写法里）
"""

from errors import SchemeError
from lexer import tokenize
from values import Pair, Symbol


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_all(self):
        """解析出全部顶层表达式。"""
        exprs = []
        while self._peek() is not None:
            exprs.append(self._parse_expr())
        return exprs

    def _parse_expr(self):
        tok = self._peek()
        if tok is None:
            raise SchemeError("程序意外结束，缺少表达式")

        if tok.kind == "'":
            self._advance()
            return [Symbol("quote"), self._parse_expr()]
        if tok.kind == "(":
            return self._parse_list()
        if tok.kind == ")":
            raise SchemeError("多余的右括号", tok.line)

        self._advance()
        return tok.value

    def _parse_list(self):
        """解析 ``(...)``；支持 ``(1 2 3)`` 与点对 ``(1 2 . 3)``。"""
        open_tok = self._advance()  # '('
        items = []
        while True:
            tok = self._peek()
            if tok is None:
                raise SchemeError("括号没有闭合", open_tok.line)
            if tok.kind == ")":
                self._advance()
                return items
            if tok.kind == ".":
                if not items:
                    raise SchemeError("'.' 出现在列表开头", tok.line)
                self._advance()
                tail = self._parse_expr()
                nxt = self._peek()
                if nxt is None or nxt.kind != ")":
                    raise SchemeError("点对缺少右括号", tok.line)
                self._advance()
                result = tail
                for item in reversed(items):
                    result = Pair(item, result)
                return result
            items.append(self._parse_expr())


def parse(source):
    """程序文本 -> 顶层表达式列表。"""
    return _Parser(tokenize(source)).parse_all()
