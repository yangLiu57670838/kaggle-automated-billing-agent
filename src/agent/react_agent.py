from decimal import Decimal, ROUND_HALF_UP

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.agent.prompts import SYSTEM_PROMPT
from src.config import load_env
from src.tools import apply_discount, calculate_final_total, calculate_subtotal


def round_money(value: float) -> float:
    """Round to 2 decimal places with financial half-up rounding."""
    return float(
        Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


class CalculateSubtotalInput(BaseModel):
    quantity: int = Field(description="Number of items ordered")
    unit_price: float = Field(description="Price per unit")


class ApplyDiscountInput(BaseModel):
    subtotal: float = Field(description="Subtotal before discount")
    discount_percent: float = Field(description="Discount percentage, e.g. 15 for 15%")


class CalculateFinalTotalInput(BaseModel):
    discounted_amount: float = Field(description="Amount after discount is applied")
    shipping_fee: float = Field(description="Delivery or freight fee")


tools = [
    StructuredTool.from_function(
        func=calculate_subtotal,
        name="calculate_subtotal",
        description="Calculate subtotal as quantity × unit_price. Call this first.",
        args_schema=CalculateSubtotalInput,
    ),
    StructuredTool.from_function(
        func=apply_discount,
        name="apply_discount",
        description="Apply discount: subtotal × (1 - discount_percent / 100). Call second.",
        args_schema=ApplyDiscountInput,
    ),
    StructuredTool.from_function(
        func=calculate_final_total,
        name="calculate_final_total",
        description="Add shipping fee to discounted amount. Call third to get Total_Bill.",
        args_schema=CalculateFinalTotalInput,
    ),
]

# use small but paid model 'gpt-4o-mini' for this simple task agent
# temperature 0: this agent is for reading email and calculate billing and discount, so no need to be too creative
def build_agent(*, model: str = "gpt-4o-mini", temperature: float = 0, debug: bool = False):
    llm = ChatOpenAI(model=model, temperature=temperature)
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=debug,
    )


def extract_total_bill(messages) -> float:
    """Return Total_Bill from the last calculate_final_total tool result.

    Intermediate tool values stay full precision; only the completed total
    is rounded to 2 decimal places (financial half-up).
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "calculate_final_total":
            return round_money(float(message.content))
    raise ValueError(
        "Agent did not call calculate_final_total; cannot determine Total_Bill"
    )


def run_billing_agent(email_text: str, *, agent=None) -> float:
    billing_agent = agent or build_agent()
    result = billing_agent.invoke({"messages": [HumanMessage(content=email_text)]})
    return extract_total_bill(result["messages"])


if __name__ == "__main__":
    load_env()
    sample_email = (
        "Hello, we would like to order 50 office chairs. The agreed price is 120 dollars per chair. "
        "We are eligible for the 15 percent bulk discount. Please include the 250 dollar delivery fee."
    )
    print(run_billing_agent(sample_email, agent=build_agent(debug=True)))
