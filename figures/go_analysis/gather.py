import pandas as pd


def main():
    samples = ["HCT116", "A549", "HepG2"]
    datasets = []

    for sample in samples:
        df = pd.read_table(f"./{sample}.txt")
        df = df.loc[:, ["Term", "PValue"]]
        df["Sample"] = sample
        datasets.append(df)

    df = pd.concat(datasets)
    print(df.to_latex(index=False))


if __name__ == "__main__":
    main()
