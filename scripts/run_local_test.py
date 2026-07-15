"""Run the billing agent on data/sample_train.csv for local evaluation."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_env
from src.pipeline.inference import run_inference, write_submission


def main() -> None:
    load_env()

    input_csv = PROJECT_ROOT / "data" / "sample_train.csv"
    output_csv = PROJECT_ROOT / "outputs" / "local_predictions.csv"

    print(f"Reading: {input_csv}")
    results = run_inference(input_csv)

    if not results:
        raise SystemExit("No rows processed from sample_train.csv")

    path = write_submission(results, output_csv)
    print(f"Wrote {len(results)} predictions to {path}")
    print("Next: python scripts/evaluate_rmse.py")


if __name__ == "__main__":
    main()
