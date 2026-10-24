"""Check cleaned hospital data before loading it."""


def check_data_quality(data):
    """Raise an error for missing IDs, duplicate IDs, or negative amounts."""
    primary_keys = {
        "patients": "patient_id",
        "appointments": "appointment_id",
        "billing": "invoice_id",
        "doctors": "doctor_id",
    }

    for name, id_column in primary_keys.items():
        table = data[name]
        if table[id_column].isna().any():
            raise ValueError(f"{name}: missing values in {id_column}")
        if table[id_column].duplicated().any():
            raise ValueError(f"{name}: duplicate values in {id_column}")

    if (data["patients"]["age"] < 0).any():
        raise ValueError("Patients contain negative ages")

    for column in ("amount_charged", "amount_paid"):
        if data["billing"][column].isna().any():
            raise ValueError(f"Billing contains missing values in {column}")
        if (data["billing"][column] < 0).any():
            raise ValueError(f"Billing contains negative values in {column}")

    return True
