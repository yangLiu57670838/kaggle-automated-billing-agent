from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent

def search_tool(query: str) -> str:
    return f"[Search results for '{query}']"

def calc_tool(expr: str) -> str:
    try:
        return str(eval(expr))
    except Exception as e:
        return f"Error: {e}"

tools = [
    Tool(name="Search", func=search_tool, description="Search documents or web for facts"),
    Tool(name="Calculator", func=calc_tool, description="Evaluate arithmetic expressions")
]

llm = ChatOpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

print(agent.run("What's the population of France, and what's 10% of it?"))