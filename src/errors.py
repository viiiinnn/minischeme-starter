"""解释器自身的错误类型。

测试用例不会触发错误，这里只保证出错时给出清晰的诊断信息，
而不是让 Python 抛出难懂的内部异常。
"""


class SchemeError(Exception):
    """mini-Scheme 求值/解析过程中出现的错误。"""

    def __init__(self, message, line=None):
        self.line = line
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
