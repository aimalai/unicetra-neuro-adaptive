import glob
import os
from math import pi
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# 1. Locate the file correctly (checking subfolder or current directory)
possible_paths = [
    r"C:\Users\Samsa\.vscode\coding\unicetra-neuro-adaptive\Master's Thesis of Malaiappan Srinivasan (24-723-686)(1-24).xlsx",
    r"Master's Thesis of Malaiappan Srinivasan (24-723-686)(1-24).xlsx",
    r"unicetra-neuro-adaptive\Master's Thesis of Malaiappan Srinivasan (24-723-686)(1-24).xlsx",
]

target_file = None
for p in possible_paths:
  # Check with glob wildcard to handle space encodings (\xa0)
  matched = glob.glob(p.replace("Malaiappan", "*Malaiappan*"))
  if matched:
    target_file = matched[0]
    break

if not target_file:
  # Fallback to general search
  all_files = glob.glob("**/*1-24*.xlsx", recursive=True)
  if all_files:
    target_file = all_files[0]

if not target_file or not os.path.exists(target_file):
  raise FileNotFoundError(
      "Could not locate the Excel file. Please ensure 'Master's Thesis of"
      " Malaiappan Srinivasan (24-723-686)(1-24).xlsx' is in your working"
      " directory."
  )

print(f"Successfully loaded file from: {target_file}")
df = pd.read_excel(target_file, sheet_name="Sheet1")

# 2. Clean & Rename Columns
suspicious_col = df.columns[11]
clean_cols = {
    "Please enter Participant ID /(e.g., P01-Baseline or P01-Occo)": (
        "Participant_ID"
    ),
    "Evaluation Condition": "Condition",
    "I am confident in the system.": "Confident",
    "The system is reliable.": "Reliable",
    "The system has integrity.": "Integrity",
    suspicious_col: "Suspicious",
    "I can trust the system.": "Trust",
}
df_clean = df.rename(columns=clean_cols)

baseline_df = df_clean[
    df_clean["Condition"].str.contains("Baseline", case=False, na=False)
].copy()
occo_df = df_clean[
    df_clean["Condition"].str.contains("Occo", case=False, na=False)
].copy()

metrics = ["Confident", "Reliable", "Integrity", "Suspicious", "Trust"]

# 3. Statistical Analysis (Paired t-tests & descriptive stats)
print("--- EMPIRICAL EVALUATION RESULTS (N=12 EXPERTS) ---")
for m in metrics:
  b_vals = baseline_df[m].values
  o_vals = occo_df[m].values
  t_stat, t_pval = stats.ttest_rel(b_vals, o_vals)
  print(
      f"Metric: {m:10s} | Baseline: {b_vals.mean():.2f} (±{b_vals.std():.2f})"
      f" | Occo: {o_vals.mean():.2f} (±{o_vals.std():.2f}) | Delta:"
      f" {o_vals.mean() - b_vals.mean():+.2f} | p-value: {t_pval:.5f}"
  )

# Set global theme
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

# --- CHART 1: Comparative Bar Plot with Error Bars ---
metrics_labels = [
    "Confident",
    "Reliable",
    "Integrity",
    "Suspicious\n(Reverse)",
    "Trust",
]
x = np.arange(len(metrics_labels))
width = 0.35

b_means = [baseline_df[m].mean() for m in metrics]
o_means = [occo_df[m].mean() for m in metrics]
b_stds = [baseline_df[m].std() for m in metrics]
o_stds = [occo_df[m].std() for m in metrics]

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
rects1 = ax.bar(
    x - width / 2,
    b_means,
    width,
    yerr=b_stds,
    label="Standard RAG Baseline",
    color="#d97706",
    alpha=0.85,
    capsize=5,
    edgecolor="black",
    linewidth=0.8,
)
rects2 = ax.bar(
    x + width / 2,
    o_means,
    width,
    yerr=o_stds,
    label="Occo AI Framework RAG",
    color="#2563eb",
    alpha=0.85,
    capsize=5,
    edgecolor="black",
    linewidth=0.8,
)

ax.set_ylabel("Mean Likert Score (1 - 7)", fontsize=12, fontweight="bold")
ax.set_title(
    "Comparative Analysis of Trust Scale Metrics (N=12 Legal Experts)",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
ax.set_xticks(x)
ax.set_xticklabels(metrics_labels, fontsize=11, fontweight="bold")
ax.legend(fontsize=11, frameon=True, facecolor="white", edgecolor="none")
ax.set_ylim(0, 8.5)


def autolabel(rects):
  for rect in rects:
    height = rect.get_height()
    ax.annotate(
        f"{height:.2f}",
        xy=(rect.get_x() + rect.get_width() / 2, height),
        xytext=(0, 6),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )


autolabel(rects1)
autolabel(rects2)
plt.tight_layout()
plt.savefig("occo_trust_comparison_barplot.png")
plt.close()

# --- CHART 2: Boxplot Distribution ---
plt.figure(figsize=(12, 6), dpi=300)
melted_df = pd.melt(
    df_clean,
    id_vars=["Participant_ID", "Condition"],
    value_vars=["Confident", "Reliable", "Integrity", "Suspicious", "Trust"],
    var_name="Metric",
    value_name="Score",
)
sns.boxplot(
    x="Metric",
    y="Score",
    hue="Condition",
    data=melted_df,
    palette=["#f59e0b", "#3b82f6"],
    boxprops=dict(alpha=0.8),
)
plt.title(
    "Distribution of Jian et al. (2000) Trust Scale Scores (Baseline vs. Occo"
    " AI)",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
plt.xlabel("Evaluation Metric", fontsize=12, fontweight="bold")
plt.ylabel("Likert Scale Rating (1-7)", fontsize=12, fontweight="bold")
plt.ylim(0.5, 8.0)
plt.legend(
    title="Evaluation Condition", fontsize=11, title_fontsize=11, loc="upper right"
)
plt.tight_layout()
plt.savefig("occo_trust_boxplot.png")
plt.close()

# --- CHART 3: Individual Participant Deltas (Trust) ---
participant_deltas = []
for i in range(12):
  b_row = baseline_df.iloc[i]
  o_row = occo_df.iloc[i]
  p_delta_val = o_row["Trust"] - b_row["Trust"]
  participant_deltas.append(
      {"Participant": f"P{i+1:02d}", "Delta": p_delta_val}
  )

p_delta_df = pd.DataFrame(participant_deltas).sort_values(
    by="Delta", ascending=False
)
plt.figure(figsize=(10, 6), dpi=300)
colors = [
    "#10b981" if d > 0 else "#ef4444" if d < 0 else "#9ca3af"
    for d in p_delta_df["Delta"]
]
plt.bar(
    p_delta_df["Participant"],
    p_delta_df["Delta"],
    color=colors,
    edgecolor="black",
    alpha=0.85,
    width=0.6,
)
plt.axhline(0, color="black", linewidth=1)
plt.title(
    "Individual Participant Overall Trust Deltas (Occo AI minus Baseline)",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
plt.xlabel("Participant ID", fontsize=12, fontweight="bold")
plt.ylabel(r"Trust Score Delta ($\Delta$)", fontsize=12, fontweight="bold")
plt.ylim(-2, 6)

for idx, row in enumerate(p_delta_df.itertuples()):
  val = row.Delta
  plt.text(
      idx,
      val + (0.2 if val >= 0 else -0.4),
      f"{val:+d}",
      ha="center",
      va="bottom" if val >= 0 else "top",
      fontweight="bold",
      fontsize=10,
  )

plt.tight_layout()
plt.savefig("occo_participant_deltas.png")
plt.close()

# --- CHART 4: Radar Chart / Spider Plot ---
categories = ["Confident", "Reliable", "Integrity", "Suspicious (Rev)", "Trust"]
b_radar = [
    baseline_df["Confident"].mean(),
    baseline_df["Reliable"].mean(),
    baseline_df["Integrity"].mean(),
    8 - baseline_df["Suspicious"].mean(),
    baseline_df["Trust"].mean(),
]
o_radar = [
    occo_df["Confident"].mean(),
    occo_df["Reliable"].mean(),
    occo_df["Integrity"].mean(),
    8 - occo_df["Suspicious"].mean(),
    occo_df["Trust"].mean(),
]

angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
angles += angles[:1]
b_radar += b_radar[:1]
o_radar += o_radar[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), dpi=300)
plt.xticks(angles[:-1], categories, color="black", size=11, fontweight="bold")
ax.set_rlabel_position(0)
plt.yticks(
    [1, 2, 3, 4, 5, 6, 7], ["1", "2", "3", "4", "5", "6", "7"], color="grey", size=8
)
plt.ylim(0, 7)

ax.plot(
    angles,
    b_radar,
    linewidth=2,
    linestyle="solid",
    label="Standard RAG Baseline",
    color="#d97706",
)
ax.fill(angles, b_radar, "#d97706", alpha=0.25)
ax.plot(
    angles,
    o_radar,
    linewidth=2,
    linestyle="solid",
    label="Occo AI Framework",
    color="#2563eb",
)
ax.fill(angles, o_radar, "#2563eb", alpha=0.25)

plt.title(
    "Multi-Dimensional Trust Profile (Jian et al. Construct Mapping)",
    size=14,
    fontweight="bold",
    pad=20,
)
plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1), fontsize=11)
plt.tight_layout()
plt.savefig("occo_trust_radar_chart.png")
plt.close()

print(
    "All 4 publication-quality charts successfully generated and saved to root!"
)