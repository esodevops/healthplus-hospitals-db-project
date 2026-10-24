"""Export the cleaned hospital records to CSV files."""

from pathlib import Path

from src.ingestion import PROJECT_ROOT
from src.quality import check_data_quality


def extract_data(data=None, output_dir=None):
    """Clean raw data, save the four CSV files, and return the cleaned frames."""
    cleaned_data = check_data_quality(data)
    output_dir = Path(output_dir) if output_dir is not None else PROJECT_ROOT / "data/cleaned_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, frame in cleaned_data.items():
        frame.to_csv(output_dir / f"{name}_cleaned.csv", index=False)

    return cleaned_data
