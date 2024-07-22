#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ===============================================================================
#
#         FILE: test.py
#
#        USAGE: ./test.py
#
#  DESCRIPTION:
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Tingyou Wang (tywang@northwestern.edu),
# ORGANIZATION: Northwestern University
#      VERSION: 2.0
#      CREATED: Wed Apr 30 13:27:17 CDT 2022
#     REVISION: ---
# ===============================================================================
import sys
import re
import os
import argparse
import pandas as pd
import numpy as np
import glob
import matplotlib

matplotlib.use("Agg")
from matplotlib import rcParams
# Set global font properties to Arial
rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": "Arial",
        "pdf.fonttype": 42,  # Embed fonts as Type 3 fonts for compatibility
        "ps.fonttype": 42,
        "text.usetex": False,
        "svg.fonttype": "none",
    }
)

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from scipy.stats import ranksums,wilcoxon,ttest_ind,mannwhitneyu,pearsonr,spearmanr,f_oneway,kruskal

sns.set(font_scale=1.0, style="ticks", palette="muted", color_codes=True)


def box_plot(data, figure_name):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Plot histogram
    sns.boxplot(x='group', y='exp', width=0.3, data=data, ax=ax, fill=False, whis=100000, showcaps=False)

    # Set labels and title
    # ax.set_xlabel("Gene effective size")
    ax.set_xlabel("")
    ax.set_ylabel("Gene expression level")
    ax.set_title("")


    #ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    ax.minorticks_off()
    # ax.set_xlim(0, 20000)
    ax.set_yscale('log')

    # Add legend
    # ax.legend()

    sns.despine(trim=True, left=False)
    fig.tight_layout(w_pad=1.1)
    fig.savefig(
        f"{figure_name}",
        dpi=300,
        facecolor="w",
        edgecolor="w",
        bbox_inches="tight",
    )
    plt.close()


def data_preparation(all_file, target_file, col_name):
    all_genes = pd.read_csv(all_file, sep="\t", index_col=0)
    target_genes = pd.read_csv(target_file, sep="\t", index_col=0)
    all_data = list(all_genes[col_name])
    target_data = list(target_genes[col_name])

    data = pd.DataFrame(
        {
            "exp": np.concatenate([all_data, target_data]),
            "group": ["all_genes"] * len(all_data)
            + ["target_genes"] * len(target_data),
        }
    )
    all_exp = data[data["group"] == "all_genes"]["exp"]
    target_exp = data[data["group"] == "target_genes"]["exp"]

    print(mannwhitneyu(target_exp, all_exp, alternative="greater"))

    return data


def main(all_file, target_file, col_name, figure_name):
    data = data_preparation(all_file, target_file, col_name)
    box_plot(data, figure_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-a", "--all", action="store", dest="all_data", help="", required=True
    )
    parser.add_argument(
        "-t", "--target", action="store", dest="target_data", help="", required=True
    )

    parser.add_argument(
        "-o",
        "--output",
        action="store",
        dest="output",
        help="(default: %(default)s)",
        default="output.pdf",
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    main(
        all_file=args.all_data,
        target_file=args.target_data,
        col_name="exp_count",
        figure_name=args.output,
    )
