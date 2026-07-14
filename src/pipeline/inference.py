import csv
import re
from pathlib import Path

from src.agent.react_agent import build_agent, run_billing_agent

_FLOAT_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_total_bill(agent_response: str) -> float:
    """Extract Total_Bill as the last float in the agent's final message."""
    text = agent_response if isinstance(agent_response, str) else str(agent_response)
    matches = _FLOAT_RE.findall(text)
    if not matches:
        raise ValueError(f"Could not parse Total_Bill from agent response: {text!r}")
    return float(matches[-1])


def run_inference(
    input_csv: str | Path,
    *,
    agent=None,
) -> list[dict[str, int | float]]:
    """
    Read order emails from CSV and compute Total_Bill for each row.

    Expected columns: order_id, email_text
    Returns: list of {"order_id": int, "Total_Bill": float}
    """
    input_path = Path(input_csv)
    billing_agent = agent or build_agent()
    results: list[dict[str, int | float]] = []

    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "order_id" not in reader.fieldnames or "email_text" not in reader.fieldnames:
            raise ValueError("Input CSV must include columns: order_id, email_text")

        for row in reader:
            order_id = int(row["order_id"])
            email_text = row["email_text"]
            response = run_billing_agent(email_text, agent=billing_agent)
            total_bill = parse_total_bill(response)
            results.append({"order_id": order_id, "Total_Bill": total_bill})
            print(f"order_id={order_id} Total_Bill={total_bill}")

    return results


def write_submission(results: list[dict[str, int | float]], output_csv: str | Path) -> Path:
    """Write submission.csv with columns order_id, Total_Bill."""
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "Total_Bill"])
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "order_id": row["order_id"],
                    "Total_Bill": row["Total_Bill"],
                }
            )

    return output_path
