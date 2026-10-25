"""
SAGE Data Analysis & Scientific Computation Subsystem
Enables SAGE to run genuine statistical tests, descriptive statistics, and plot publication-quality charts.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt

from tools.artifacts import artifact_vault
from config.settings import settings


class ScientificDataAnalyzer:
    """Scientific research, data analysis, and statistical hypothesis testing."""

    def __init__(self, agent_id: str = "dot-sage-02"):
        self.agent_id = agent_id

    def analyze_dataset_stats(
        self,
        filepath_or_data: Any,
        numeric_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parses a dataset (CSV, JSON, or list of dicts) and calculates complete descriptive statistics.
        """
        try:
            if isinstance(filepath_or_data, str) and (filepath_or_data.endswith(".csv") or filepath_or_data.endswith(".json")):
                path = Path(filepath_or_data)
                if not path.is_absolute():
                    path = settings.DATA_DIR / "sandboxes" / self.agent_id / filepath_or_data
                if filepath_or_data.endswith(".csv"):
                    df = pd.read_csv(str(path))
                else:
                    df = pd.read_json(str(path))
            elif isinstance(filepath_or_data, list):
                df = pd.DataFrame(filepath_or_data)
            elif isinstance(filepath_or_data, pd.DataFrame):
                df = filepath_or_data
            else:
                return {"success": False, "error": "Unsupported data format"}

            cols = numeric_columns or df.select_dtypes(include=[np.number]).columns.tolist()
            if not cols:
                return {"success": False, "error": "No numeric columns found for statistical calculation"}

            stats_dict = {}
            for col in cols:
                series = df[col].dropna()
                if len(series) == 0:
                    continue
                q25, q75 = np.percentile(series, [25, 75])
                iqr = q75 - q25
                outliers_count = int(((series < (q25 - 1.5 * iqr)) | (series > (q75 + 1.5 * iqr))).sum())
                
                stats_dict[col] = {
                    "count": int(series.count()),
                    "mean": float(round(series.mean(), 4)),
                    "std_dev": float(round(series.std(), 4)),
                    "median": float(round(series.median(), 4)),
                    "min": float(round(series.min(), 4)),
                    "max": float(round(series.max(), 4)),
                    "iqr": float(round(iqr, 4)),
                    "skewness": float(round(series.skew(), 4)) if len(series) > 2 else 0.0,
                    "outliers_count": outliers_count,
                }

            return {
                "success": True,
                "total_rows": len(df),
                "analyzed_columns": cols,
                "descriptive_statistics": stats_dict,
            }
        except Exception as e:
            return {"success": False, "error": f"Analysis failed: {str(e)}"}

    def run_hypothesis_test(
        self,
        group_a: List[float],
        group_b: List[float],
        test_type: str = "welch_t_test",
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Runs rigorous statistical hypothesis testing:
        - "welch_t_test": Independent two-sample t-test without assumption of equal variance.
        - "mann_whitney": Non-parametric test for ordinal or non-normal continuous data.
        """
        try:
            arr_a = np.array(group_a, dtype=float)
            arr_b = np.array(group_b, dtype=float)

            if len(arr_a) < 2 or len(arr_b) < 2:
                return {"success": False, "error": "Each cohort must contain at least 2 observations"}

            mean_a, mean_b = float(np.mean(arr_a)), float(np.mean(arr_b))
            std_a, std_b = float(np.std(arr_a, ddof=1)), float(np.std(arr_b, ddof=1))

            if test_type.lower() == "mann_whitney":
                res = stats.mannwhitneyu(arr_a, arr_b)
                stat_name = "U-statistic"
            else:
                res = stats.ttest_ind(arr_a, arr_b, equal_var=False)
                stat_name = "Welch's t-statistic"

            stat_val = float(round(res.statistic, 4))
            p_val = float(round(res.pvalue, 6))
            is_significant = p_val < alpha

            interpretation = (
                f"Statistically significant difference detected (p = {p_val} < {alpha}). "
                f"Cohort A (mean={mean_a:.2f}, std={std_a:.2f}) vs Cohort B (mean={mean_b:.2f}, std={std_b:.2f})."
                if is_significant else
                f"No statistically significant difference detected (p = {p_val} >= {alpha}). "
                f"Fail to reject the null hypothesis."
            )

            return {
                "success": True,
                "test_name": stat_name,
                "statistic": stat_val,
                "p_value": p_val,
                "alpha": alpha,
                "significant": is_significant,
                "cohort_a": {"count": len(arr_a), "mean": round(mean_a, 4), "std": round(std_a, 4)},
                "cohort_b": {"count": len(arr_b), "mean": round(mean_b, 4), "std": round(std_b, 4)},
                "interpretation": interpretation,
            }
        except Exception as e:
            return {"success": False, "error": f"Hypothesis testing error: {str(e)}"}

    def run_one_way_anova(
        self,
        groups: Dict[str, List[float]],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """Runs One-Way ANOVA across 3 or more groups."""
        try:
            group_arrays = [np.array(v, dtype=float) for v in groups.values()]
            res = stats.f_oneway(*group_arrays)
            f_stat = float(round(res.statistic, 4))
            p_val = float(round(res.pvalue, 6))
            significant = p_val < alpha

            group_summaries = {}
            for name, vals in groups.items():
                arr = np.array(vals, dtype=float)
                group_summaries[name] = {
                    "count": len(arr),
                    "mean": float(round(np.mean(arr), 4)),
                    "std": float(round(np.std(arr, ddof=1), 4)) if len(arr) > 1 else 0.0
                }

            return {
                "success": True,
                "test_name": "One-Way ANOVA",
                "f_statistic": f_stat,
                "p_value": p_val,
                "significant": significant,
                "groups": group_summaries,
                "interpretation": (
                    f"Significant variance across groups found (F = {f_stat}, p = {p_val} < {alpha})."
                    if significant else
                    f"No statistically significant difference among group means (F = {f_stat}, p = {p_val} >= {alpha})."
                )
            }
        except Exception as e:
            return {"success": False, "error": f"ANOVA test error: {str(e)}"}

    def generate_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        title: str,
        filename: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates clean, publication-ready PNG charts:
        - "bar": categories and values
        - "line": x_values, y_values (multiple lines supported)
        - "histogram": data_series, bins
        - "scatter": x_values, y_values
        """
        try:
            plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
            fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)

            clean_type = chart_type.lower()
            if clean_type == "bar":
                labels = data.get("labels", [])
                values = data.get("values", [])
                color = data.get("color", "#2563eb")
                bars = ax.bar(labels, values, color=color, alpha=0.88, edgecolor="#1e3a8a", width=0.6)
                for bar in bars:
                    yval = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2.0, yval, f"{yval:g}", ha="center", va="bottom", fontsize=10, fontweight="bold")
                ax.set_ylabel(data.get("y_label", "Value"), fontsize=11, fontweight="medium")

            elif clean_type == "line":
                x = data.get("x", [])
                series_map = data.get("series", {"Primary": data.get("y", [])})
                for s_name, y_vals in series_map.items():
                    ax.plot(x, y_vals, marker="o", linewidth=2.2, label=s_name)
                ax.set_xlabel(data.get("x_label", "Time / Index"), fontsize=11)
                ax.set_ylabel(data.get("y_label", "Value"), fontsize=11)
                if len(series_map) > 1:
                    ax.legend(frameon=True)

            elif clean_type == "histogram":
                vals = data.get("values", [])
                bins = data.get("bins", 15)
                ax.hist(vals, bins=bins, color="#10b981", alpha=0.75, edgecolor="#065f46")
                ax.set_xlabel(data.get("x_label", "Distribution"), fontsize=11)
                ax.set_ylabel("Frequency", fontsize=11)

            elif clean_type == "scatter":
                x = data.get("x", [])
                y = data.get("y", [])
                ax.scatter(x, y, color="#8b5cf6", alpha=0.8, edgecolors="#4c1d95", s=50)
                ax.set_xlabel(data.get("x_label", "X"), fontsize=11)
                ax.set_ylabel(data.get("y_label", "Y"), fontsize=11)

            ax.set_title(title, fontsize=14, fontweight="bold", pad=12, color="#0f172a")
            ax.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()

            # Save PNG
            out_filename = filename or f"{title.lower().replace(' ', '_')[:25]}_{clean_type}.png"
            if not out_filename.endswith(".png"):
                out_filename += ".png"

            out_path = settings.DATA_DIR / "sandboxes" / self.agent_id / out_filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(str(out_path), bbox_inches="tight")
            plt.close(fig)

            artifact = artifact_vault.register_file(
                agent_id=self.agent_id,
                name=out_filename,
                source_path=out_path,
                task_id=task_id,
                file_type="png",
                metadata={"chart_type": clean_type, "title": title},
            )

            return {
                "success": True,
                "artifact_id": artifact.id,
                "filename": out_filename,
                "file_path": artifact.file_path,
                "download_url": f"/api/artifacts/{artifact.id}/download",
                "message": f"Chart '{title}' generated and saved as {out_filename}."
            }
        except Exception as e:
            plt.close("all")
            return {"success": False, "error": f"Chart rendering failed: {str(e)}"}
