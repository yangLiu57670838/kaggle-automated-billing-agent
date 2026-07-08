import ast
import operator

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_arithmetic(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_arithmetic(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_arithmetic(node.left), _eval_arithmetic(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARYOPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_arithmetic(node.operand))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


class CalculatorInput(BaseModel):
    expr: str = Field(
        description="Arithmetic expression to evaluate, e.g. '50 * 120' or '6000 * 0.15'"
    )


def search_tool(query: str) -> str:
    return f"[Search results for '{query}']"


def calc_tool(expr: str) -> str:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
        return str(_eval_arithmetic(tree))
    except Exception as e:
        return f"Error: {e}"


tools = [
    Tool(name="Search", func=search_tool, description="Search documents or web for facts"),
    Tool(
        name="Calculator",
        func=calc_tool,
        description="Evaluate arithmetic expressions using +, -, *, /, %, **, and parentheses.",
        args_schema=CalculatorInput,
    ),
]

llm = ChatOpenAI(
    model="gpt-4o-mini", # use small but paid model for this simple task agent
    temperature=0 ## this agent is for reading email and calculate billing and discount, so no need to be too creative
)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

print(agent.run("What's the population of France, and what's 10% of it?"))
