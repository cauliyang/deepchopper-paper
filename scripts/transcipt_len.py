# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "gtfparse",
#     "numpy<2",
#     "polars",
#     "typer",
#     "pandas",
# ]
# ///

import typer
from gtfparse import read_gtf
from pathlib import Path
import polars as pl

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


def get_all_transcript_lengths(
    gtf_file: Path,
    output_file: Path | None = None,
    gene_biotype: str = "protein_coding",
):
    """
    Extract all transcripts with their lengths (sum of exon and UTRs) for each gene.
    Outputs one row per transcript: gene_id, transcript_id, transcript_length, gene_length, gene_name, chromosome, strand
    """
    # Read GTF
    df = read_gtf(str(gtf_file))

    # Calculate gene length (span from min start to max end for each gene)
    gene_lengths = (
        df.filter(pl.col("gene_id").is_not_null())
        .group_by("gene_id")
        .agg([(pl.col("end").max() - pl.col("start").min() + 1).alias("gene_length")])
    )

    # Features to include for transcript length
    exonic_features = set(
        f.lower() for f in ["exon", "five_prime_utr", "three_prime_utr", "3utr", "5utr"]
    )

    # Lowercase for filtering
    df = df.with_columns(
        pl.col("feature").cast(str).str.to_lowercase().alias("_feature_lc")
    )
    exons_utrs = df.filter(pl.col("_feature_lc").is_in(exonic_features))

    # Filter by gene_biotype if specified
    if gene_biotype is not None:
        if "gene_biotype" in exons_utrs.columns:
            exons_utrs = exons_utrs.filter(pl.col("gene_biotype") == gene_biotype)

    # Filter out rows with missing transcript_id or gene_id
    exons_utrs = exons_utrs.filter(
        pl.col("transcript_id").is_not_null() & pl.col("gene_id").is_not_null()
    )

    if len(exons_utrs) == 0:
        raise ValueError(
            f"No exonic features found matching the criteria in {gtf_file}"
        )

    # Calculate region length and remove bad
    exons_utrs = exons_utrs.with_columns(
        (pl.col("end") - pl.col("start") + 1).alias("region_length")
    ).filter(pl.col("region_length") > 0)

    # Sum region_length per transcript
    agg_exprs = [
        pl.col("region_length").sum().alias("transcript_length"),
        pl.col("seqname").first().alias("chromosome"),
        pl.col("strand").first().alias("strand"),
    ]

    # Add gene_name if it exists
    if "gene_name" in exons_utrs.columns:
        agg_exprs.append(pl.col("gene_name").first().alias("gene_name"))
    else:
        agg_exprs.append(pl.lit("").alias("gene_name"))

    trans_lengths = exons_utrs.group_by("transcript_id", "gene_id").agg(agg_exprs)

    # Join gene lengths to transcript data
    trans_lengths = trans_lengths.join(gene_lengths, on="gene_id", how="left")

    # Sort by gene_id and transcript_length (descending)
    result = trans_lengths.sort(
        ["gene_id", "transcript_length", "transcript_id"],
        descending=[False, True, False],
    )

    # Select and order columns
    outcols = [
        "gene_id",
        "transcript_id",
        "transcript_length",
        "gene_length",
        "gene_name",
        "chromosome",
        "strand",
    ]
    result = result.select([c for c in outcols if c in result.columns])

    # Output to file or stdout
    if output_file:
        result.write_csv(str(output_file), separator="\t")
    else:
        print("\t".join(result.columns))
        for row in result.iter_rows(named=True):
            print("\t".join(str(row.get(col, "")) for col in result.columns))


@app.command()
def main(
    gtf_file: Path = typer.Argument(..., help="Path to the GTF file", exists=True),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file path to save results as a TSV table"
    ),
    gene_biotype: str = typer.Option(
        "protein_coding",
        "--biotype",
        "-b",
        help="Filter by gene biotype (default: protein_coding)",
    ),
):
    """
    Extract all transcripts with their lengths (sum of exonic and UTR parts) for all genes.
    Output includes: gene_id, transcript_id, transcript_length, gene_length, gene_name, chromosome, strand
    """
    get_all_transcript_lengths(gtf_file, output, gene_biotype)


if __name__ == "__main__":
    app()
