"""求值器：表达式 -> 值（解释器的心脏）。

evaluate 与 apply_proc 互相递归：
- evaluate 遇到函数调用就求值操作符与实参，交给 apply_proc
- apply_proc 执行用户函数体时又回到 evaluate
"""

from environment import Environment
from errors import SchemeError
from printer import to_string
from values import (
    Builtin,
    Pair,
    Procedure,
    Symbol,
    datumize,
    is_truthy,
)


def evaluate(expr, env):
    """求值一个表达式。"""
    if isinstance(expr, Symbol):
        return env.lookup(expr)
    if isinstance(expr, list):
        return _eval_combination(expr, env)
    if isinstance(expr, Pair):
        raise SchemeError("点对表达式需要加 quote 才是数据")
    # 自求值：整数、浮点、字符串、布尔、空表
    return expr


def apply_proc(proc, args):
    """调用一个过程：内置的直接执行，闭包则新建一层环境。"""
    if isinstance(proc, Builtin):
        return proc.fn(args)
    if isinstance(proc, Procedure):
        if len(args) != len(proc.params):
            raise SchemeError(
                f"参数个数不匹配: 期望 {len(proc.params)}, 得到 {len(args)}"
            )
        frame = Environment(proc.env)  # 外层指向定义时的环境（词法作用域）
        for name, value in zip(proc.params, args):
            frame.define(name, value)
        return _eval_body(proc.body, frame)
    raise SchemeError(f"无法调用该对象: {to_string(proc)}")


def _eval_body(body, env):
    """按 begin 语义依次求值，返回最后一个结果（空体返回 None）。"""
    result = None
    for expr in body:
        result = evaluate(expr, env)
    return result


def _eval_combination(expr, env):
    head = expr[0]
    if isinstance(head, Symbol) and head in _SPECIALS:
        return _SPECIALS[head](expr[1:], env)

    proc = evaluate(head, env)
    args = [evaluate(item, env) for item in expr[1:]]  # 应用序：先求值全部实参
    return apply_proc(proc, args)


def _eval_quote(rest, env):
    if len(rest) != 1:
        raise SchemeError("quote: 需要 1 个参数")
    return datumize(rest[0])


def _eval_if(rest, env):
    if len(rest) not in (2, 3):
        raise SchemeError("if: 需要 2 或 3 个参数")
    if is_truthy(evaluate(rest[0], env)):
        return evaluate(rest[1], env)
    if len(rest) == 3:
        return evaluate(rest[2], env)
    return None  # 假分支省略时结果无值


def _eval_cond(rest, env):
    for clause in rest:
        if not isinstance(clause, list) or not clause:
            raise SchemeError("cond: 非法子句")
        test = clause[0]
        if isinstance(test, Symbol) and test == "else":
            value = True  # else 兜底，不再求值
        else:
            value = evaluate(test, env)
        if is_truthy(value):
            if len(clause) == 1:  # 无表达式时返回测试值本身
                return value
            return _eval_body(clause[1:], env)
    return None  # 全部不匹配


def _eval_and(rest, env):
    result = True
    for item in rest:
        result = evaluate(item, env)
        if result is False:  # 短路：后面的表达式不再执行
            return False
    return result


def _eval_or(rest, env):
    for item in rest:
        result = evaluate(item, env)
        if result is not False:
            return result
    return False


def _eval_define(rest, env):
    if len(rest) < 2:
        raise SchemeError("define: 参数个数不足")
    target = rest[0]

    if isinstance(target, list):  # (define (f x) 体...)
        if not target:
            raise SchemeError("define: 缺少函数名")
        name = target[0]
        if not isinstance(name, Symbol):
            raise SchemeError("define: 函数名必须是符号")
        params = []
        for param in target[1:]:
            if not isinstance(param, Symbol):
                raise SchemeError("define: 参数必须是符号")
            params.append(param)
        # 先构造闭包再绑定，闭包引用同一个 env 对象，因此函数体能看到自己
        env.define(name, Procedure(params, rest[1:], env))
        return name

    if not isinstance(target, Symbol):
        raise SchemeError("define: 名字必须是符号")
    if len(rest) != 2:
        raise SchemeError("define: 形式应为 (define 名 表达式)")
    value = evaluate(rest[1], env)  # 先求值右侧，再绑定
    env.define(target, value)
    return target


def _eval_lambda(rest, env):
    if len(rest) < 2:
        raise SchemeError("lambda: 需要参数列表与函数体")
    params_expr = rest[0]
    if not isinstance(params_expr, list):
        raise SchemeError("lambda: 参数列表必须是 (...) 形式")
    params = []
    for param in params_expr:
        if not isinstance(param, Symbol):
            raise SchemeError("lambda: 参数必须是符号")
        params.append(param)
    # 函数体此时不求值，闭包记住定义时的环境
    return Procedure(params, rest[1:], env)


def _eval_let(rest, env):
    if len(rest) < 2:
        raise SchemeError("let: 需要绑定列表与函数体")
    bindings = rest[0]
    if not isinstance(bindings, list):
        raise SchemeError("let: 绑定必须是 ((名 表达式)...) 形式")

    names, values = [], []
    for binding in bindings:
        if not isinstance(binding, list) or len(binding) != 2:
            raise SchemeError("let: 每个绑定必须是 (名 表达式)")
        if not isinstance(binding[0], Symbol):
            raise SchemeError("let: 绑定的名字必须是符号")
        names.append(binding[0])
        values.append(evaluate(binding[1], env))  # 并行绑定：都在外层环境求值

    frame = Environment(env)
    for name, value in zip(names, values):
        frame.define(name, value)
    return _eval_body(rest[1:], frame)


def _eval_begin(rest, env):
    if not rest:
        return None
    return _eval_body(rest, env)


#: 特殊形式 -> 处理函数（每个函数接收剩余参数与当前环境）
_SPECIALS = {
    "quote": _eval_quote,
    "if": _eval_if,
    "cond": _eval_cond,
    "and": _eval_and,
    "or": _eval_or,
    "define": _eval_define,
    "lambda": _eval_lambda,
    "let": _eval_let,
    "begin": _eval_begin,
}
