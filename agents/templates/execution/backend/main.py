"""{{AGENT_NAME}} — execution 유형: 제한된 실행기. 기본 구현은 AST 화이트리스트 산술식 계산(임의 코드 실행 없음).
실제 코드 샌드박스(gVisor·microsandbox)는 X05 에서 별 컨테이너로 붙인다."""
import ast
import math
import operator as op

from agentplaza_sdk import Agent, CapabilityError, create_app

agent = Agent.from_manifest("agent.yaml")

OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Mod: op.mod,
       ast.Pow: op.pow, ast.USub: op.neg, ast.UAdd: op.pos, ast.FloorDiv: op.floordiv}
FUNCS = {"sqrt": math.sqrt, "abs": abs, "round": round, "min": min, "max": max, "log": math.log}
MAX_POW = 1000


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POW:
            raise CapabilityError("exponent too large")
        return OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
        return FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise CapabilityError(f"unsupported expression: {type(node).__name__}")


@agent.capability("calculate")
def calculate(payload: dict, ctx):
    expr = payload["expression"]
    if len(expr) > 200:
        raise CapabilityError("expression too long")
    try:
        return {"value": _eval(ast.parse(expr, mode="eval"))}
    except (SyntaxError, ZeroDivisionError, OverflowError, ValueError) as exc:
        raise CapabilityError(f"cannot evaluate: {exc}") from None


app = create_app(agent)
