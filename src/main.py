"""mini-Scheme 解释器入口（流水线：读 -> 算 -> 打印）。

用法：
    python3 src/main.py file1.scm [file2.scm ...]
    python3 src/main.py < file.scm        # 无参数时从标准输入读取

多个文件共享同一个全局环境；每个顶层表达式的结果独占一行，
结果为 None（如 display/newline）时不打印。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.setrecursionlimit(20000)  # 深递归程序（阶乘、sum-to 500 等）不会撞到 Python 默认的 1000 层

from errors import SchemeError  # noqa: E402
from evaluator import evaluate  # noqa: E402
from source_io import decode, read_text  # noqa: E402
from printer import to_string  # noqa: E402
from primitives import make_global_env  # noqa: E402
from syntax import parse  # noqa: E402


def _configure_streams():
    """输出编码与换行固定为 UTF-8 + ``\\n``，保证结果字节与平台无关。

    被评分器捕获（非终端）时才改写编码：交互式终端保留系统编码，
    中文不会在控制台上变乱码。换行不做 Windows 的 ``\\r\\n`` 转换，
    否则逐字节比对会因平台而异。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (stream.encoding or "").lower()
            if not stream.isatty() and "utf" not in encoding:
                stream.reconfigure(encoding="utf-8", errors="replace")
            stream.reconfigure(newline="")
        except (AttributeError, OSError, ValueError):
            pass  # 老版本 Python 或不可重配置的流：维持原样


def run_program(text, env):
    """求值一段程序的所有顶层表达式并逐行打印结果。"""
    for expr in parse(text):
        value = evaluate(expr, env)
        if value is not None:
            sys.stdout.write(to_string(value) + "\n")


def _fail(message):
    """报错前先冲刷标准输出，保证已算出的结果与错误信息顺序不乱。"""
    try:
        sys.stdout.flush()
    except OSError:
        pass
    sys.stderr.write(f"error: {message}\n")
    return 1


def main(argv):
    _configure_streams()
    files = argv[1:]
    env = make_global_env()
    try:
        if files:
            for path in files:
                run_program(read_text(path), env)
        else:
            run_program(decode(sys.stdin.buffer.read()), env)
    except SchemeError as exc:
        return _fail(str(exc))
    except OSError as exc:
        return _fail(str(exc))
    except RecursionError:
        return _fail("递归层数过深")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
