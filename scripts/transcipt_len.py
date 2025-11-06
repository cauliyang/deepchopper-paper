# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "gtfparse",
#     "numpy<2",
#     "polars",
#     "typer",
# ]
# ///

import typer
from gtfparse import read_gtf
from pathlib import Path
import polars as pl

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


def get_transcript_lengths(
    gtf_file: Path,
    output_file: Path | None = None,
    gene_biotype: str | None = None,
    show_stats: bool = False,
    max_only: bool = False,
):
    """
    Calculate transcript lengths and genomic spans from a GTF file.

    For each transcript, calculates:
    - transcript_length: sum of all exon lengths (spliced/mature transcript)
    - genomic_span: total span in genome including introns (end - start + 1)
    """

    # Read GTF file and filter for exons
    df = read_gtf(gtf_file)
    exons = df.filter(pl.col("feature") == "exon")

    # Show gene biotype statistics if requested
    if show_stats:
        gene_info = df.filter(pl.col("feature") == "gene")
        if "gene_biotype" in gene_info.columns:
            biotype_counts = (
                gene_info.group_by("gene_biotype")
                .agg(pl.count().alias("count"))
                .sort("count", descending=True)
            )
            typer.echo("\n=== Gene Biotype Statistics ===")
            for row in biotype_counts.iter_rows(named=True):
                typer.echo(f"{row['gene_biotype']}: {row['count']}")
            typer.echo(f"\nTotal genes: {gene_info.height}")
            typer.echo("================================\n")

    # Filter by gene biotype if specified
    if gene_biotype:
        if "gene_biotype" in exons.columns:
            exons = exons.filter(pl.col("gene_biotype") == gene_biotype)
            typer.echo(f"Filtering for gene_biotype: {gene_biotype}")
        else:
            typer.echo("Warning: 'gene_biotype' column not found in GTF file", err=True)

    # Calculate exon lengths and genomic span by transcript
    agg_cols = [
        pl.col("exon_length").sum().alias("transcript_length"),
        pl.col("gene_id").first(),
        pl.col("gene_name").first(),
        pl.col("seqname").first().alias("chromosome"),
        pl.col("strand").first(),
        pl.col("start").min().alias("genomic_start"),
        pl.col("end").max().alias("genomic_end"),
    ]

    # Include gene_biotype if available
    if "gene_biotype" in exons.columns:
        agg_cols.append(pl.col("gene_biotype").first())

    transcript_lengths = (
        exons.with_columns((pl.col("end") - pl.col("start") + 1).alias("exon_length"))
        .group_by("transcript_id")
        .agg(agg_cols)
        .with_columns(
            (pl.col("genomic_end") - pl.col("genomic_start") + 1).alias("genomic_span")
        )
        .sort(["gene_id", "transcript_id"])
    )

    if max_only:
        # Find maximum transcript length per gene
        gene_agg = [
            pl.col("transcript_length").max().alias("max_transcript_length"),
            pl.col("genomic_span").max().alias("max_genomic_span"),
            pl.col("gene_name").first().alias("gene_name"),
            pl.col("chromosome").first(),
            pl.col("strand").first(),
        ]

        # Include gene_biotype if available
        if "gene_biotype" in transcript_lengths.columns:
            gene_agg.append(pl.col("gene_biotype").first().alias("gene_biotype"))

        result = transcript_lengths.group_by("gene_id").agg(gene_agg).sort("gene_id")
        typer.echo(f"Total genes processed: {result.height}")
    else:
        # Return all transcripts
        result = transcript_lengths
        num_genes = result.select("gene_id").n_unique()
        typer.echo(f"Total transcripts: {result.height}, across {num_genes} genes")

    # Save to file or print to stdout
    if output_file:
        result.write_csv(output_file, separator="\t")
        typer.echo(f"Results saved to {output_file}")
    else:
        for row in result.iter_rows(named=True):
            if max_only:
                print(f"{row['gene_id']}\t{row['max_transcript_length']}")
            else:
                print(
                    f"{row['transcript_id']}\t{row['gene_id']}\t{row['transcript_length']}"
                )


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
        help="Filter by gene biotype (e.g., 'protein_coding')",
    ),
    show_stats: bool = typer.Option(
        False, "--stats", "-s", help="Show gene biotype statistics"
    ),
    max_only: bool = typer.Option(
        False,
        "--max-only",
        "-m",
        help="Output only maximum transcript length per gene (default: all transcripts)",
    ),
):
    """
    Calculate transcript lengths and genomic spans from a GTF file.

    By default, outputs all transcripts with their lengths grouped by gene.
    Use --max-only to get only the maximum transcript length per gene.

    Output columns:
    - transcript_id: Ensembl transcript ID
    - gene_id: Ensembl gene ID
    - gene_name: Gene symbol
    - chromosome: Chromosome/contig name
    - strand: + or -
    - transcript_length: Sum of all exon lengths (spliced length)
    - genomic_span: Genomic span from first to last position (includes introns)
    - genomic_start: Start position in genome
    - genomic_end: End position in genome
    - gene_biotype: Gene biotype (if available)

    Examples:

    # Show statistics about gene types
    uv run script.py input.gtf --stats

    # Get all transcript lengths for protein-coding genes
    uv run script.py input.gtf -o transcripts.tsv --biotype protein_coding

    # Get maximum transcript length per gene only
    uv run script.py input.gtf -o max_lengths.tsv --biotype protein_coding --max-only
    """
    get_transcript_lengths(gtf_file, output, gene_biotype, show_stats, max_only)


if __name__ == "__main__":
    app()
