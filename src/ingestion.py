"""Read the four raw hospital datasets."""

from pathlib import Path

import pandas as pd

# Find the project folder so paths work from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def data_ingestion(data_dir=None):
    """Read each CSV file and return the four tables in a dictionary."""
    # Use the project's raw data folder unless another folder is provided.
    if data_dir is None:
        data_dir = PROJECT_ROOT / "data" / "raw_data"
    else:
        data_dir = Path(data_dir)

    # Read each CSV into its own Pandas DataFrame (a table of rows and columns).
    patients = pd.read_csv(data_dir / "patients.csv")
    appointments = pd.read_csv(data_dir / "appointments.csv")
    billing = pd.read_csv(data_dir / "billing.csv")
    doctors = pd.read_csv(data_dir / "doctors.csv")

    # Keep the tables together so the cleaning step can access them by name.
    return {
        "patients": patients,
        "appointments": appointments,
        "billing": billing,
        "doctors": doctors,
    }
