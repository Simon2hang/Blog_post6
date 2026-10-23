from pathlib import Path
import sqlite3
import pandas as pd



DATA = Path("data/processed_data")

IND_FILE = DATA / "individual_core.csv"
PID_FILE = DATA / "parent_links.csv"
INCOME_FILE = DATA / "family_income.csv"

DB_FILE = DATA / "psid_blog6.sqlite"


individual = pd.read_csv(IND_FILE)

parent_links = pd.read_csv(PID_FILE)

family_income = pd.read_csv(INCOME_FILE)


print("Individuals:", individual.shape)
print("Parent links:", parent_links.shape)
print("Family income:", family_income.shape)


con = sqlite3.connect(DB_FILE)


individual.to_sql(
    "individual",
    con,
    if_exists="replace",
    index=False
)


parent_links.to_sql(
    "parent_links",
    con,
    if_exists="replace",
    index=False
)


family_income.to_sql(
    "family_income",
    con,
    if_exists="replace",
    index=False
)


print("\nSQLite database created.")


# ============================================================

con.execute(
    "DROP TABLE IF EXISTS parent_pairs"
)


con.execute("""
CREATE TABLE parent_pairs AS


SELECT DISTINCT

    child_id,

    mother_id AS parent_id,

    'mother' AS parent_role

FROM parent_links

WHERE
    mother_1968_id > 0
    AND mother_person_num > 0


UNION ALL


SELECT DISTINCT

    child_id,

    father_id AS parent_id,

    'father' AS parent_role

FROM parent_links

WHERE
    father_1968_id > 0
    AND father_person_num > 0
""")


con.commit()


parent_check = pd.read_sql_query("""
SELECT

    parent_role,

    COUNT(*) AS number_of_links

FROM parent_pairs

GROUP BY parent_role
""", con)


print("\nParent-child links:")
print(parent_check)


# ============================================================


con.execute(
    "DROP TABLE IF EXISTS person_year_income"
)


con.execute("""
CREATE TABLE person_year_income AS



SELECT

    i.person_id,

    2016 AS income_year,

    i.age_2017 AS age,

    i.family_id_2017 AS family_id,

    i.sequence_2017 AS sequence_number,

    i.relation_2017 AS relationship,


    CASE

        WHEN
            i.sequence_2017 = 1
            AND i.relation_2017 = 10

        THEN f.ref_income_2016


        WHEN
            i.sequence_2017 = 2
            AND i.relation_2017 IN (20, 22)

        THEN f.spouse_income_2016


        ELSE NULL

    END AS personal_labor_income,


    CASE

        WHEN
            i.sequence_2017 = 1
            AND i.relation_2017 = 10

        THEN 'reference_person'


        WHEN
            i.sequence_2017 = 2
            AND i.relation_2017 IN (20, 22)

        THEN 'spouse_partner'


        ELSE 'other'

    END AS income_role


FROM individual AS i

LEFT JOIN family_income AS f

    ON i.family_id_2017 = f.family_id_2017



UNION ALL




SELECT

    i.person_id,

    2018 AS income_year,

    i.age_2019 AS age,

    i.family_id_2019 AS family_id,

    i.sequence_2019 AS sequence_number,

    i.relation_2019 AS relationship,


    CASE

        WHEN
            i.sequence_2019 = 1
            AND i.relation_2019 = 10

        THEN f.ref_income_2018


        WHEN
            i.sequence_2019 = 2
            AND i.relation_2019 IN (20, 22)

        THEN f.spouse_income_2018


        ELSE NULL

    END AS personal_labor_income,


    CASE

        WHEN
            i.sequence_2019 = 1
            AND i.relation_2019 = 10

        THEN 'reference_person'


        WHEN
            i.sequence_2019 = 2
            AND i.relation_2019 IN (20, 22)

        THEN 'spouse_partner'


        ELSE 'other'

    END AS income_role


FROM individual AS i

LEFT JOIN family_income AS f

    ON i.family_id_2019 = f.family_id_2019



UNION ALL



SELECT

    i.person_id,

    2020 AS income_year,

    i.age_2021 AS age,

    i.family_id_2021 AS family_id,

    i.sequence_2021 AS sequence_number,

    i.relation_2021 AS relationship,


    CASE

        WHEN
            i.sequence_2021 = 1
            AND i.relation_2021 = 10

        THEN f.ref_income_2020


        WHEN
            i.sequence_2021 = 2
            AND i.relation_2021 IN (20, 22)

        THEN f.spouse_income_2020


        ELSE NULL

    END AS personal_labor_income,


    CASE

        WHEN
            i.sequence_2021 = 1
            AND i.relation_2021 = 10

        THEN 'reference_person'


        WHEN
            i.sequence_2021 = 2
            AND i.relation_2021 IN (20, 22)

        THEN 'spouse_partner'


        ELSE 'other'

    END AS income_role


FROM individual AS i

LEFT JOIN family_income AS f

    ON i.family_id_2021 = f.family_id_2021



UNION ALL




SELECT

    i.person_id,

    2022 AS income_year,

    i.age_2023 AS age,

    i.family_id_2023 AS family_id,

    i.sequence_2023 AS sequence_number,

    i.relation_2023 AS relationship,


    CASE

        WHEN
            i.sequence_2023 = 1
            AND i.relation_2023 = 10

        THEN f.ref_income_2022


        WHEN
            i.sequence_2023 = 2
            AND i.relation_2023 IN (20, 22)

        THEN f.spouse_income_2022


        ELSE NULL

    END AS personal_labor_income,


    CASE

        WHEN
            i.sequence_2023 = 1
            AND i.relation_2023 = 10

        THEN 'reference_person'


        WHEN
            i.sequence_2023 = 2
            AND i.relation_2023 IN (20, 22)

        THEN 'spouse_partner'


        ELSE 'other'

    END AS income_role


FROM individual AS i

LEFT JOIN family_income AS f

    ON i.family_id_2023 = f.family_id_2023
""")


con.commit()



role_check = pd.read_sql_query("""
SELECT

    income_year,

    income_role,

    COUNT(*) AS observations,

    SUM(
        CASE
            WHEN personal_labor_income IS NOT NULL
            THEN 1
            ELSE 0
        END
    ) AS income_observed

FROM person_year_income

GROUP BY
    income_year,
    income_role

ORDER BY
    income_year,
    income_role
""", con)


print("\nPersonal income assignment:")
print(role_check)


con.execute(
    "DROP TABLE IF EXISTS matched_parent_rows"
)


con.execute("""
CREATE TABLE matched_parent_rows AS


SELECT

    pp.child_id,

    pp.parent_id,

    pp.parent_role,

    c.income_year,


    c.age AS child_age,

    p.age AS parent_age,


    c.personal_labor_income AS child_income,

    p.personal_labor_income AS parent_income


FROM parent_pairs AS pp


INNER JOIN person_year_income AS c

    ON pp.child_id = c.person_id


INNER JOIN person_year_income AS p

    ON pp.parent_id = p.person_id

    AND c.income_year = p.income_year


WHERE

    c.personal_labor_income IS NOT NULL

    AND p.personal_labor_income IS NOT NULL
""")


con.commit()


# ============================================================


con.execute(
    "DROP TABLE IF EXISTS matched_yearly_income"
)


con.execute("""
CREATE TABLE matched_yearly_income AS


SELECT

    child_id,

    income_year,


    MAX(child_age)
        AS child_age,


    AVG(parent_age)
        AS parent_age,


    MAX(child_income)
        AS child_income,


    SUM(parent_income)
        AS parent_income,


    COUNT(DISTINCT parent_id)
        AS parents_observed


FROM matched_parent_rows


GROUP BY

    child_id,

    income_year
""")


con.commit()


# ============================================================


yearly = pd.read_sql_query("""
SELECT *

FROM matched_yearly_income

ORDER BY
    child_id,
    income_year
""", con)


# ============================================================


single_year = pd.read_sql_query("""
SELECT

    child_id,

    child_age,

    parent_age,

    child_income,

    parent_income,

    parents_observed


FROM matched_yearly_income


WHERE

    income_year = 2022

    AND child_age BETWEEN 25 AND 55

    AND child_income > 0

    AND parent_income > 0
""", con)


# ============================================================


multi_year = pd.read_sql_query("""
SELECT

    child_id,


    AVG(child_income)
        AS child_income_avg,


    AVG(parent_income)
        AS parent_income_avg,


    AVG(child_age)
        AS child_age_avg,


    AVG(parent_age)
        AS parent_age_avg,


    AVG(parents_observed)
        AS parents_observed_avg,


    COUNT(*)
        AS years_observed


FROM matched_yearly_income


WHERE

    child_age BETWEEN 25 AND 55

    AND child_income > 0

    AND parent_income > 0


GROUP BY

    child_id


HAVING

    COUNT(*) >= 3
""", con)



yearly.to_csv(
    DATA / "matched_yearly_income.csv",
    index=False
)


single_year.to_csv(
    DATA / "matched_single_year_2022.csv",
    index=False
)


multi_year.to_csv(
    DATA / "matched_multiyear_income.csv",
    index=False
)


# Optional diagnostic file

person_year = pd.read_sql_query("""
SELECT *

FROM person_year_income

WHERE personal_labor_income IS NOT NULL
""", con)


person_year.to_csv(
    DATA / "person_year_personal_income.csv",
    index=False
)



print("\n" + "=" * 60)

print("CORRECTED SQL MATCHING COMPLETE")

print("=" * 60)


print(
    "\nAll matched child-year observations:",
    len(yearly)
)


print(
    "Single-year 2022 adult sample:",
    len(single_year)
)


print(
    "Multi-year adult sample:",
    len(multi_year)
)


print("\nSingle-year child age range:")

print(
    single_year["child_age"].min(),
    "to",
    single_year["child_age"].max()
)


print("\nSingle-year sample:")

print(
    single_year.head()
)



print("\nMulti-year sample:")

print(
    multi_year.head()
)


year_check = pd.read_sql_query("""
SELECT

    income_year,

    COUNT(*) AS matched_observations,

    SUM(
        CASE
            WHEN child_age BETWEEN 25 AND 55
                 AND child_income > 0
                 AND parent_income > 0
            THEN 1
            ELSE 0
        END
    ) AS analysis_observations,


    AVG(
        CASE
            WHEN child_age BETWEEN 25 AND 55
                 AND child_income > 0
                 AND parent_income > 0
            THEN child_income
        END
    ) AS mean_child_income,


    AVG(
        CASE
            WHEN child_age BETWEEN 25 AND 55
                 AND child_income > 0
                 AND parent_income > 0
            THEN parent_income
        END
    ) AS mean_parent_income


FROM matched_yearly_income


GROUP BY income_year


ORDER BY income_year
""", con)


print("\nObservations by year:")

print(year_check)


con.close()


print(
    "\nCorrected files saved in data/processed_data/"
)
