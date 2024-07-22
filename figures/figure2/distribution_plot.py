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
import seaborn as sns

sns.set(font_scale=1.0, style="ticks", palette="muted", color_codes=True)


def distribution_plot(data1, data2, figure_name):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Plot histogram
    sns.histplot(data1, kde=False, color="#80E3F4", label="All genes", ax=ax, binwidth=500)
    sns.histplot(data2, kde=False, color="#974CF1", label="Target genes", ax=ax, binwidth=500)

    #sns.histplot(data1, kde=False, color="blue", label="All genes", ax=ax, binwidth=1000)
    #sns.histplot(data2, kde=False, color="red", label="Target genes", ax=ax, binwidth=1000)

    # Set labels and title
    ax.set_xlabel("Gene effective size")
    #ax.set_xlabel("Gene expression level")
    ax.set_ylabel("Frequency")
    ax.set_title("")

    ax.set_xlim(0, 20000)
    #ax.set_xscale('log')

    # Add legend
    ax.legend()

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

    return all_data, target_data


def main(all_file, target_file, col_name, figure_name):
    all_data, target_data = data_preparation(all_file, target_file, col_name)
    distribution_plot(all_data, target_data, figure_name)

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

    main(all_file=args.all_data, target_file=args.target_data, col_name="maximum_effective_size", figure_name=args.output)
    #main(all_file=args.all_data, target_file=args.target_data, col_name="exp_count", figure_name=args.output)
