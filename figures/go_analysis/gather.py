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

    return df


def main():
    samples = ["HCT116", "A549", "HepG2"]
    df = gather(samples)
    styler = df.style

    latex = styler.to_latex()
    print(latex)


if __name__ == "__main__":
    main()
