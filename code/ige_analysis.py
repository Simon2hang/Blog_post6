from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


DATA = Path("data/processed_data")
FIG = Path("figures")

FIG.mkdir(parents=True, exist_ok=True)

YEARLY_FILE = DATA / "matched_yearly_income.csv"

df = pd.read_csv(YEARLY_FILE)

print("Matched yearly data:", df.shape)


cpi = {
    2016: 240.007,
    2018: 251.107,
    2020: 258.811,
    2022: 292.655
}

CPI_2022 = cpi[2022]


df["inflation_factor"] = (
    df["income_year"]
    .map(lambda year: CPI_2022 / cpi[year])
)


df["child_income_real"] = (
    df["child_income"]
    * df["inflation_factor"]
)


df["parent_income_real"] = (
    df["parent_income"]
    * df["inflation_factor"]
)


analysis = df[
    (df["child_age"] >= 25)
    & (df["child_age"] <= 55)
    & (df["child_income_real"] > 0)
    & (df["parent_income_real"] > 0)
].copy()


print(
    "Valid adult child-year observations:",
    len(analysis)
)


def estimate_ige(data, child_col, parent_col):

    temp = data[
        [child_col, parent_col]
    ].dropna().copy()

    temp = temp[
        (temp[child_col] > 0)
        & (temp[parent_col] > 0)
    ]

    temp["log_child"] = np.log(
        temp[child_col]
    )

    temp["log_parent"] = np.log(
        temp[parent_col]
    )

    X = sm.add_constant(
        temp["log_parent"]
    )

    model = sm.OLS(
        temp["log_child"],
        X
    ).fit(
        cov_type="HC1"
    )

    beta = model.params["log_parent"]

    se = model.bse["log_parent"]

    lower = beta - 1.96 * se
    upper = beta + 1.96 * se

    return {
        "ige": beta,
        "standard_error": se,
        "ci_lower": lower,
        "ci_upper": upper,
        "p_value": model.pvalues["log_parent"],
        "n": len(temp),
        "r_squared": model.rsquared,
        "model": model
    }



single_year = analysis[
    analysis["income_year"] == 2022
].copy()


single_result = estimate_ige(
    single_year,
    "child_income_real",
    "parent_income_real"
)


print("\n" + "=" * 60)
print("SINGLE-YEAR IGE — 2022")
print("=" * 60)

print(
    "IGE:",
    round(single_result["ige"], 4)
)

print(
    "Standard error:",
    round(single_result["standard_error"], 4)
)

print(
    "95% CI:",
    round(single_result["ci_lower"], 4),
    "to",
    round(single_result["ci_upper"], 4)
)

print(
    "N:",
    single_result["n"]
)

print(
    "R-squared:",
    round(single_result["r_squared"], 4)
)



multi_year = (
    analysis
    .groupby("child_id")
    .agg(
        child_income_avg=(
            "child_income_real",
            "mean"
        ),

        parent_income_avg=(
            "parent_income_real",
            "mean"
        ),

        child_age_avg=(
            "child_age",
            "mean"
        ),

        parent_age_avg=(
            "parent_age",
            "mean"
        ),

        years_observed=(
            "income_year",
            "count"
        )
    )
    .reset_index()
)


multi_year = multi_year[
    multi_year["years_observed"] >= 3
].copy()


multi_year.to_csv(
    DATA / "matched_multiyear_real_income.csv",
    index=False
)


print(
    "\nMulti-year sample:",
    len(multi_year)
)



multi_result = estimate_ige(
    multi_year,
    "child_income_avg",
    "parent_income_avg"
)


print("\n" + "=" * 60)
print("MULTI-YEAR IGE")
print("=" * 60)

print(
    "IGE:",
    round(multi_result["ige"], 4)
)

print(
    "Standard error:",
    round(multi_result["standard_error"], 4)
)

print(
    "95% CI:",
    round(multi_result["ci_lower"], 4),
    "to",
    round(multi_result["ci_upper"], 4)
)

print(
    "N:",
    multi_result["n"]
)

print(
    "R-squared:",
    round(multi_result["r_squared"], 4)
)


results = pd.DataFrame({

    "measure": [
        "Single-year income (2022)",
        "Multi-year average income"
    ],

    "ige": [
        single_result["ige"],
        multi_result["ige"]
    ],

    "standard_error": [
        single_result["standard_error"],
        multi_result["standard_error"]
    ],

    "ci_lower": [
        single_result["ci_lower"],
        multi_result["ci_lower"]
    ],

    "ci_upper": [
        single_result["ci_upper"],
        multi_result["ci_upper"]
    ],

    "n": [
        single_result["n"],
        multi_result["n"]
    ],

    "r_squared": [
        single_result["r_squared"],
        multi_result["r_squared"]
    ]
})


results.to_csv(
    DATA / "ige_results.csv",
    index=False
)


print("\nIGE comparison:")
print(results)


single_year["age_group"] = pd.cut(

    single_year["child_age"],

    bins=[
        25,
        30,
        35,
        40,
        45,
        56
    ],

    right=False,

    labels=[
        "25–29",
        "30–34",
        "35–39",
        "40–44",
        "45–55"
    ]
)


age_results = []


for group in single_year["age_group"].dropna().unique():

    subset = single_year[
        single_year["age_group"] == group
    ]

    if len(subset) < 30:
        continue

    result = estimate_ige(
        subset,
        "child_income_real",
        "parent_income_real"
    )

    age_results.append({

        "age_group": str(group),

        "ige": result["ige"],

        "standard_error":
            result["standard_error"],

        "ci_lower":
            result["ci_lower"],

        "ci_upper":
            result["ci_upper"],

        "n":
            result["n"]
    })


age_results = pd.DataFrame(
    age_results
)


age_order = [
    "25–29",
    "30–34",
    "35–39",
    "40–44",
    "45–55"
]


age_results["age_group"] = pd.Categorical(
    age_results["age_group"],
    categories=age_order,
    ordered=True
)


age_results = age_results.sort_values(
    "age_group"
)


age_results.to_csv(
    DATA / "ige_by_age_group.csv",
    index=False
)


print("\n" + "=" * 60)
print("IGE BY CHILD AGE GROUP")
print("=" * 60)

print(age_results)


fig, ax = plt.subplots(
    figsize=(8, 5)
)


x = np.arange(
    len(results)
)


ax.bar(
    x,
    results["ige"]
)


errors = [
    results["ige"] - results["ci_lower"],
    results["ci_upper"] - results["ige"]
]


ax.errorbar(
    x,
    results["ige"],
    yerr=errors,
    fmt="none",
    capsize=5
)


ax.set_xticks(x)

ax.set_xticklabels(
    [
        "Single-Year\n2022",
        "Multi-Year\nAverage"
    ]
)


ax.set_ylabel(
    "Intergenerational Elasticity (IGE)"
)


ax.set_title(
    "Single-Year vs. Multi-Year Income Measures"
)


ax.axhline(
    0,
    linewidth=0.8
)


fig.tight_layout()


fig.savefig(
    FIG / "ige_single_vs_multiyear.png",
    dpi=300
)


plt.close(fig)


fig, ax = plt.subplots(
    figsize=(9, 5)
)


x = np.arange(
    len(age_results)
)


ax.plot(
    x,
    age_results["ige"],
    marker="o"
)


ax.fill_between(
    x,
    age_results["ci_lower"],
    age_results["ci_upper"],
    alpha=0.2
)


ax.axhline(
    multi_result["ige"],
    linestyle="--",
    label="Multi-year IGE"
)


ax.set_xticks(x)

ax.set_xticklabels(
    age_results["age_group"]
)


ax.set_xlabel(
    "Child Age in 2023"
)


ax.set_ylabel(
    "Single-Year IGE"
)


ax.set_title(
    "Single-Year IGE Changes Across the Life Cycle"
)


ax.legend()


fig.tight_layout()


fig.savefig(
    FIG / "ige_by_age_group.png",
    dpi=300
)


plt.close(fig)



plot_data = single_year.copy()


plot_data["log_parent_income"] = np.log(
    plot_data["parent_income_real"]
)


plot_data["log_child_income"] = np.log(
    plot_data["child_income_real"]
)


fig, ax = plt.subplots(
    figsize=(8, 6)
)


ax.scatter(
    plot_data["log_parent_income"],
    plot_data["log_child_income"],
    alpha=0.25
)


x_line = np.linspace(
    plot_data["log_parent_income"].min(),
    plot_data["log_parent_income"].max(),
    100
)


y_line = (
    single_result["model"].params["const"]
    +
    single_result["ige"] * x_line
)


ax.plot(
    x_line,
    y_line
)


ax.set_xlabel(
    "Log Parental Labor Income"
)


ax.set_ylabel(
    "Log Child Labor Income"
)


ax.set_title(
    "Parent and Child Labor Income in 2022"
)


fig.tight_layout()


fig.savefig(
    FIG / "parent_child_income_2022.png",
    dpi=300
)


plt.close(fig)



print("\n" + "=" * 60)

print("IGE ANALYSIS COMPLETE")

print("=" * 60)

print(
    "\nSingle-year IGE:",
    round(single_result["ige"], 3)
)

print(
    "Multi-year IGE:",
    round(multi_result["ige"], 3)
)

print(
    "\nResults saved to data/processed_data/"
)

print(
    "Figures saved to figures/"
)
