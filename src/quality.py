"""Clean hospital records with the notebook's basic Pandas commands."""

import pandas as pd

from src.ingestion import data_ingestion


def check_data_quality(data=None):
    """Return cleaned copies of the supplied datasets (or read the raw CSVs)."""
    if data is None:
        data = data_ingestion()
    patients = data["patients"].copy()
    appointments = data["appointments"].copy()
    billing = data["billing"].copy()
    doctors = data["doctors"].copy()

    # Removing duplicates from the patients dataset
    patients = patients.drop_duplicates().copy()

    # Standardizing the city names in the patients dataset 
    patients["city"] = patients["city"].str.title()


    # Standardize gender values in the patients dataset
    patients["gender"] = patients["gender"].replace({
        "M":"Male",
        "F":"Female",
        "male":"Male",
        "female":"Female"
    })

    # Filling missing gender nan
    patients["gender"] = patients["gender"].fillna("Unknown")

    # Replacing missing emails with a placeholder value
    patients["email"] = patients["email"].fillna("Not Provided")

    # Converting the age values to integers/numeric 
    patients["age"] = pd.to_numeric(
        patients["age"], 
        errors="coerce" #Replace anything that cannot be converted to a number with NaN(Not a Number). Invalid age become NaN
    )

    # Replace missing age values 
    patients["age"] = patients["age"].fillna(
        patients["age"].median()
    )

    # Replace negative ages with missing values
    patients.loc[patients["age"] < 0, "age"] = pd.NA

    # Fill missing values with the median
    patients["age"] = patients["age"].fillna(
        patients["age"].median()
    )

    # Round ages
    patients["age"] = patients["age"].round()

    # Convert to integers
    patients["age"] = patients["age"].astype(int)

    # Find missing IDs
    missing_rows = patients[patients["patient_id"].isna()].index

    # Generate new IDs
    max_patient_id = patients["patient_id"].dropna().str[1:].astype(int).max()
    max_patient_id = 0 if pd.isna(max_patient_id) else int(max_patient_id)
    for i, idx in enumerate(missing_rows, start=max_patient_id + 1):
        patients.loc[idx, "patient_id"] = f"P{i:05d}"

    # Standardize names to Title Case
    patients["full_name"] = patients["full_name"].str.title() 

    # Fill the missing values in the phone_number column with "Unknown"
    patients["phone_number"] = patients["phone_number"].fillna("Unknown")

    # Remove spaces from phone numbers so they use one consistent format
    patients["phone_number"] = patients["phone_number"].str.replace(" ", "", regex=False)

    # Remove hyphens from phone numbers
    patients["phone_number"] = patients["phone_number"].str.replace("-", "", regex=False)

    # Change Nigeria's +234 country code to a leading zero
    """ 
    Skipping the first four characters of the phone number (which is +234) and adding a leading zero to the remaining part of the phone number.
    """
    patients["phone_number"] = patients["phone_number"].apply(
        lambda x: "0" + x[4:] if x.startswith("+234") else x
    )

    # Add a leading zero to local phone numbers that contain 10 characters
    patients["phone_number"] = patients["phone_number"].apply(
        lambda phone: "0" + phone if len(phone) == 10 else phone
    )

    # Replace a known invalid placeholder with the standard value, Unknown
    patients["phone_number"] = patients["phone_number"].replace({
        "not_available": "Unknown"
    })

    # Replace invalid phone numbers
    # A Nigerian phone number should contain 11 digits.
    # Anything shorter or longer is invalid.

    """
    This will automatically convert:
    12345 into Unknown

    while leaving 08026951234 unchanged.
    """

    patients["phone_number"] = patients["phone_number"].apply(
        lambda phone: phone if phone == "Unknown" or len(phone) == 11 else "Unknown"
    )


    # Convert email addresses to lowercase for consistent matching
    patients["email"] = patients["email"].str.lower()

    # Standardize common missing or invalid email labels as Unknown
    patients["email"] = patients["email"].replace({
        "Not Provided": "Unknown",
        "not_an_email": "Unknown",
        "not provided": "Unknown",
        "not available": "Unknown",
        "n/a": "Unknown",
        "none": "Unknown"
    })

    # Instead of automatically fixing them (which may introduce incorrect data), mark them as unknown.
    patients["email"] = patients["email"].apply(
        lambda email: email if email == "Unknown" or "@" in email else "Unknown"
    )

    # Convert registration_date to date only
    patients["registration_date"] = (
        pd.to_datetime(
            patients["registration_date"],
            format="%Y/%m/%d",
            errors="coerce"
        )
        .dt.date
    )

    # Replace registration dates that could not be parsed with a placeholder
    patients["registration_date"] = patients["registration_date"].fillna("unknown")

    # Creating the Age group column 
    patients["age_group"] = pd.cut(
        patients["age"],
        bins=[0,17,35,60,float("inf")],
        include_lowest=True,
        labels=[
            "Child",
            "Young Adult",
            "Adult",
            "Senior"
        ]
    )

    # Find the largest appointment_id
    # Get the highest appointment number
    max_id = (
        appointments["appointment_id"]
        .dropna()
        .str.replace("A", "", regex=False)
        .astype(int)
        .max()
    )

    max_id = 0 if pd.isna(max_id) else int(max_id)

    # Generate new appointment IDs for missing values
    # Find rows with missing IDs
    missing_rows = appointments["appointment_id"].isna()

    # Create new IDs
    new_ids = [
        f"A{num:06d}"
        for num in range(max_id + 1, max_id + 1 + missing_rows.sum())
    ]

    # Assign them
    appointments.loc[missing_rows, "appointment_id"] = new_ids

    # Preserve rows with an unknown patient reference by assigning a placeholder ID
    appointments["patient_id"] = appointments["patient_id"].fillna("UNKNOWN_PATIENT")

    # Preserve rows with an unknown doctor reference by assigning a placeholder ID
    appointments["doctor_id"] = appointments["doctor_id"].fillna("UNKNOWN_DOCTOR")

    # Remove duplicate "No Show" entries from the appointments dataset
    appointments["appointment_status"] = (
        appointments["appointment_status"]
        .astype("string")
        .str.strip()  # Remove spaces from the beginning and end
        .str.replace("-", " ", regex=False)
        .str.replace("–", " ", regex=False)
        .str.replace("—", " ", regex=False)
        .str.replace("‑", " ", regex=False)
        .str.replace("  ", " ", regex=False)  # Replace double spaces
        .str.title()  # Make each word start with a capital letter
    )

    # Standardize the Status columns 
    appointments["appointment_status"] = (
        appointments["appointment_status"]
        .str.title()
    ) 

    # Fill up the 345 missing values in the appointment_status column with "Pending"
    appointments["appointment_status"] = appointments["appointment_status"].fillna("Pending")

    # Convert the appointment_date column to datetime format first
    appointments["appointment_date"] = pd.to_datetime(
        appointments["appointment_date"],
        errors="coerce",
        format="mixed"
    )

    # Standardize the format. We do not need to convert the appointment_date column to date only because it is already in the correct format. We will just standardize the format to YYYY-MM-DD.
    appointments["appointment_date"] = (
        appointments["appointment_date"]
        .dt.strftime("%Y-%m-%d")
    )


    # Fill missing visit descriptions with a consistent placeholder
    appointments["reason_for_visit"] = appointments["reason_for_visit"].fillna("Unknown")

    # remove rows with missing invoice IDs since they represent the primary key.
    billing = billing.dropna(subset=["invoice_id"]).copy()

    # The patient_id column is a foreign key. Just drop the missing values in the patient_id column since they are not many.
    billing = billing.dropna(subset=["patient_id"]).copy()

    # Parse mixed invoice-date formats and store valid dates as YYYY-MM-DD
    billing["invoice_date"] = pd.to_datetime(
        billing["invoice_date"],
        errors="coerce",
        format="mixed"
    ).dt.strftime("%Y-%m-%d")

    # Convert to Numeric  
    billing["amount_charged"] = pd.to_numeric(
        billing["amount_charged"],
        errors="coerce"
    )

    # Replace negative amounts with missing values
    billing.loc[
        billing["amount_charged"] < 0,
        "amount_charged"
    ] = pd.NA

    # Fill missing values with median 
    billing["amount_charged"] = billing["amount_charged"].fillna(
        billing["amount_charged"].median()
    )

    # Round the amount_charged to the nearest whole number
    billing["amount_charged"] = billing["amount_charged"].round().astype(int)

    # Convert to numeric first 
    billing["amount_paid"] = pd.to_numeric(
        billing["amount_paid"],
        errors="coerce"
    )


    # replace negative values if any 
    billing.loc[
        billing["amount_paid"] < 0,
        "amount_paid"
    ] = 0



    # fill missing values with 0
    billing["amount_paid"] = billing["amount_paid"].fillna(0)

    # Round to nearest whole number
    billing["amount_paid"] = billing["amount_paid"].round().astype(int)

    # Convert to title case for the payment_method column 
    billing["payment_method"] = (
        billing["payment_method"]
        .str.strip()
        .str.title()
    )  

    # Replace missing values with unknown 
    billing["payment_method"] = billing["payment_method"].fillna("Unknown")

    # Convert to title case 
    billing["payment_status"] = (
        billing["payment_status"]
        .str.strip()
        .str.title()
    )

    # Fill missing values 
    billing["payment_status"] = billing["payment_status"].fillna("Unknown")

    # Get the highest existing doctor number
    max_id = (
        doctors["doctor_id"]
        .dropna()
        .str.replace("D", "", regex=False)
        .astype(int)
        .max()
    )

    max_id = 0 if pd.isna(max_id) else int(max_id)

    # Find rows with missing doctor_id
    missing_rows = doctors["doctor_id"].isna()

    # Generate new doctor IDs
    new_ids = [
        f"D{num:04d}"
        for num in range(max_id + 1, max_id + 1 + missing_rows.sum())
    ]

    # Assign the new IDs
    doctors.loc[missing_rows, "doctor_id"] = new_ids

    # Remove extra spaces and standardize doctor names to title case
    doctors["doctor_name"] = (
        doctors["doctor_name"]
        .str.strip()
        .str.title()
    )

    # Remove extra spaces and standardize specialty names to title case
    doctors["specialty"] = (
        doctors["specialty"]
        .str.strip()
        .str.title()
    )

    # Fill the missing values in the specialty with unknown
    doctors["specialty"] = doctors["specialty"].fillna("Unknown")

    # Standardize Capitalization 
    doctors["branch"] = (
        doctors["branch"]
        .str.strip()
        .str.title()
    )

    # Fill Missing Values in the branch column with "Unknown" 
    doctors["branch"] = doctors["branch"].fillna("Unknown")

    return {
        "patients": patients,
        "appointments": appointments,
        "billing": billing,
        "doctors": doctors,
    }
