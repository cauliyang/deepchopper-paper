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
def find(bam: Path):
    """
    Find the internal adapters in a BAM file.
    """
    typer.echo(f"Finding internal adapters in {bam}...")
    typer.echo("Reading BAM file...")
    bam = pysam.AlignmentFile(bam, "rb")
    for read in bam:
        if "I" in read.query_name and not read.has_tag("SA"):
            print(read.query_name)

if __name__ == "__main__":
    app()