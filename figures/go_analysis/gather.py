import pandas as pd


def gather(samples: list[str]) -> pd.DataFrame:
    datasets = []

    for sample in samples:
        df = pd.read_table(f"./{sample}.txt")
        df = df.loc[:, ["Term", "PValue", "Genes"]]
        df["Sample"] = sample
        datasets.append(df)

    df = pd.concat(datasets)
    df = df.query("PValue < 0.05")
    df = df.reindex(
        columns=[
            "Sample",
            "Term",
            "Genes",
            "PValue",
        ]
    )

    # sort p-value among sample groups
    df = df.sort_values(["Sample", "PValue"])
    return df


def main():
    samples = ["HCT116", "A549", "HepG2", "VCaP004"]
    df = gather(samples)

    print(df)
    styler = df.style

    styler.format({"PValue": "{:.2e}"})
    latex = styler.to_latex(siunitx=True)

    print(latex)


if __name__ == "__main__":
    main()
