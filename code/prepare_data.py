from pathlib import Path
from zipfile import ZipFile
import io
import pandas as pd

RAW = Path("data/raw_data")
OUT = Path("data/processed_data")

OUT.mkdir(parents=True, exist_ok=True)

IND_ZIP = RAW / "ind2023er.zip"
PID_ZIP = RAW / "pid23.zip"
INCOME_ZIP = RAW / "J366546.zip"


def read_fwf_from_zip(zip_path, filename_end, colspecs, names):

    with ZipFile(zip_path) as z:

        matches = [
            name
            for name in z.namelist()
            if name.lower().endswith(filename_end.lower())
            and "__MACOSX" not in name
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Expected one file ending in {filename_end}, "
                f"found {matches}"
            )

        with z.open(matches[0]) as raw_file:

            text_file = io.TextIOWrapper(
                raw_file,
                encoding="utf-8"
            )

            df = pd.read_fwf(
                text_file,
                colspecs=colspecs,
                names=names
            )

    return df



print("Reading Parent Identification File...")


pid = read_fwf_from_zip(

    PID_ZIP,

    "PID23.txt",

    colspecs=[
        (1, 5),      # PID2  child 1968 interview ID
        (5, 8),      # PID3  child person number

        (8, 12),     # PID4  mother 1968 interview ID
        (12, 15),    # PID5  mother person number

        (42, 46),    # PID23 father 1968 interview ID
        (46, 49)     # PID24 father person number
    ],

    names=[
        "child_1968_id",
        "child_person_num",

        "mother_1968_id",
        "mother_person_num",

        "father_1968_id",
        "father_person_num"
    ]
)


for col in pid.columns:
    pid[col] = pd.to_numeric(
        pid[col],
        errors="coerce"
    ).astype("Int64")


# Stable IDs

pid["child_id"] = (
    pid["child_1968_id"].astype("string").str.zfill(4)
    + "_"
    + pid["child_person_num"].astype("string").str.zfill(3)
)

pid["mother_id"] = (
    pid["mother_1968_id"].astype("string").str.zfill(4)
    + "_"
    + pid["mother_person_num"].astype("string").str.zfill(3)
)

pid["father_id"] = (
    pid["father_1968_id"].astype("string").str.zfill(4)
    + "_"
    + pid["father_person_num"].astype("string").str.zfill(3)
)


parent_links = pid[
    [
        "child_1968_id",
        "child_person_num",
        "child_id",

        "mother_1968_id",
        "mother_person_num",
        "mother_id",

        "father_1968_id",
        "father_person_num",
        "father_id"
    ]
].copy()


print("Parent-link rows:", len(parent_links))


print("Reading Individual File...")


individual = read_fwf_from_zip(

    IND_ZIP,

    "IND2023ER.txt",

    colspecs=[

        # Stable person ID
        (1, 5),          # ER30001
        (5, 8),          # ER30002

        # -----------------------
        # 2017
        # -----------------------
        (4869, 4874),    # ER34501 family interview ID
        (4874, 4876),    # ER34502 sequence number
        (4876, 4878),    # ER34503 relationship
        (4878, 4881),    # ER34504 age

        # -----------------------
        # 2019
        # -----------------------
        (5249, 5254),    # ER34701
        (5254, 5256),    # ER34702
        (5256, 5258),    # ER34703
        (5258, 5261),    # ER34704

        # -----------------------
        # 2021
        # -----------------------
        (5683, 5688),    # ER34901
        (5688, 5690),    # ER34902
        (5690, 5692),    # ER34903
        (5692, 5695),    # ER34904

        # -----------------------
        # 2023
        # -----------------------
        (6118, 6123),    # ER35101
        (6123, 6125),    # ER35102
        (6125, 6127),    # ER35103
        (6127, 6130)     # ER35104
    ],

    names=[
        "person_1968_id",
        "person_num",

        "family_id_2017",
        "sequence_2017",
        "relation_2017",
        "age_2017",

        "family_id_2019",
        "sequence_2019",
        "relation_2019",
        "age_2019",

        "family_id_2021",
        "sequence_2021",
        "relation_2021",
        "age_2021",

        "family_id_2023",
        "sequence_2023",
        "relation_2023",
        "age_2023"
    ]
)


for col in individual.columns:
    individual[col] = pd.to_numeric(
        individual[col],
        errors="coerce"
    ).astype("Int64")


# Stable person ID

individual["person_id"] = (
    individual["person_1968_id"]
    .astype("string")
    .str.zfill(4)
    + "_"
    + individual["person_num"]
    .astype("string")
    .str.zfill(3)
)


individual = individual[
    [
        "person_id",
        "person_1968_id",
        "person_num",

        "family_id_2017",
        "sequence_2017",
        "relation_2017",
        "age_2017",

        "family_id_2019",
        "sequence_2019",
        "relation_2019",
        "age_2019",

        "family_id_2021",
        "sequence_2021",
        "relation_2021",
        "age_2021",

        "family_id_2023",
        "sequence_2023",
        "relation_2023",
        "age_2023"
    ]
]


print("Individual rows:", len(individual))


print("Reading Family Income File...")


with ZipFile(INCOME_ZIP) as z:

    matches = [
        name
        for name in z.namelist()
        if name.lower().endswith("j366546.xlsx")
        and "__MACOSX" not in name
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Could not uniquely find J366546.xlsx: {matches}"
        )

    excel_bytes = z.read(matches[0])


family_income = pd.read_excel(
    io.BytesIO(excel_bytes),
    engine="calamine"
)


print("Income file shape:", family_income.shape)



family_income = family_income.rename(
    columns={

        "ER66002": "family_id_2017",
        "ER71293": "ref_income_2016",
        "ER71321": "spouse_income_2016",

        "ER72002": "family_id_2019",
        "ER77315": "ref_income_2018",
        "ER77343": "spouse_income_2018",

        "ER78002": "family_id_2021",
        "ER81642": "ref_income_2020",
        "ER81670": "spouse_income_2020",

        "ER82002": "family_id_2023",
        "ER85496": "ref_income_2022",
        "ER85524": "spouse_income_2022"
    }
)


family_income = family_income[
    [
        "family_id_2017",
        "ref_income_2016",
        "spouse_income_2016",

        "family_id_2019",
        "ref_income_2018",
        "spouse_income_2018",

        "family_id_2021",
        "ref_income_2020",
        "spouse_income_2020",

        "family_id_2023",
        "ref_income_2022",
        "spouse_income_2022"
    ]
]


for col in family_income.columns:
    family_income[col] = pd.to_numeric(
        family_income[col],
        errors="coerce"
    )


parent_links.to_csv(
    OUT / "parent_links.csv",
    index=False
)

individual.to_csv(
    OUT / "individual_core.csv",
    index=False
)

family_income.to_csv(
    OUT / "family_income.csv",
    index=False
)



print("")
print("=" * 60)
print("DATA PREPARATION COMPLETE")
print("=" * 60)

print("Parent links:", parent_links.shape)
print("Individuals:", individual.shape)
print("Family income:", family_income.shape)



check_2023 = (
    individual[
        [
            "sequence_2023",
            "relation_2023"
        ]
    ]
    .value_counts()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

print("\nMost common 2023 sequence / relationship combinations:")
print(check_2023.head(10))


print("\nFiles saved in data/processed_data/")
