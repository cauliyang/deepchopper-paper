# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "typer",
#     "pyfastx",
#     "pysam",
# ]
# ///

import typer
import pyfastx
from pathlib import Path
import pysam

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def cal_internal(
    fastq_file: Path,
):
    """
    Calculate the number of internal adapters in a FASTQ file.
    """
    typer.echo(f"Calculating internal adapters for {fastq_file}...")
    typer.echo("Reading FASTQ file...")
    internal_adapters = set()
    total_reads = 0
    fastq = pyfastx.Fastx(fastq_file)

    for read_name, _seq, _qual in fastq:
        total_reads += 1
        if "I" in read_name:
            read_name_without_cut_type = read_name.split("|")[0]
            internal_adapters.add(read_name_without_cut_type)

    typer.echo(f"Total internal adapters: {len(internal_adapters)}")
    typer.echo(f"Total reads: {total_reads}")


@app.command()
def ratio(bam_before: Path, fastq_after: Path):
    """
    Calculate the ratio of internal adapters in a fastq file.

    Get the chimeric reads in bam file, and then count the number of internal adapters in the fastq file.
    Check if the reads with internal adapters of the fastq file are chimeric reads in the bam file.
    """
    typer.echo(
        f"Calculating ratio of internal adapters in {bam_before} and {fastq_after}..."
    )
    typer.echo("Reading BAM file...")
    bam = pysam.AlignmentFile(bam_before, "rb")
    fastq = pyfastx.Fastx(fastq_after)

    chimeric_reads = set()
    reads_with_internal_adapters = set()

    for read_name, _seq, _qual in fastq:
        if "I" in read_name:
            read_name_without_cut_type = read_name.split("|")[0]
            reads_with_internal_adapters.add(read_name_without_cut_type)

    typer.echo(
        f"Total reads with internal adapters: {len(reads_with_internal_adapters)}"
    )

    for read in bam:
        if read.has_tag("SA"):
            chimeric_reads.add(read.query_name)

    typer.echo(f"Total chimeric reads: {len(chimeric_reads)}")

    chimeric_reads_with_internal_adapters = reads_with_internal_adapters.intersection(
        chimeric_reads
    )
    typer.echo(
        f"Total chimeric reads with internal adapters: {len(chimeric_reads_with_internal_adapters)}"
    )

    ratio = len(chimeric_reads_with_internal_adapters) / len(chimeric_reads)
    typer.echo(f"Ratio of chimeric reads with internal adapters: {ratio:.2%}")


if __name__ == "__main__":
    app()
