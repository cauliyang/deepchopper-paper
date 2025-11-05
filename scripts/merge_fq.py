import pyfastx
import gzip
import typer
from rich.progress import track

from pathlib import Path

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

@app.command()
def merge_fastq(
    fastq1: Path,
    fastq2: Path,
    output_fq_gz: Path,
):
    """
    Merge two FASTQ files into one gzipped FASTQ file using pyfastx.
    """
    typer.echo(f"Merging {fastq1} and {fastq2} into {output_fq_gz}...")
    with gzip.open(output_fq_gz, 'wt') as out_f:

        for fq_path in [fastq1, fastq2]:
            fq_iter = pyfastx.Fastx(fq_path)
            for name, seq, qual in track(fq_iter, description="Merging FASTQ files..."):
                out_f.write(f"@{name}\n{seq}\n+\n{qual}\n")

if __name__ == "__main__":
    app()