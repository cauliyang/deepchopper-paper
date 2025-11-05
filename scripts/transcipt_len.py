# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "gtfparse",
#     "numpy<2",
#     "pandas",
#     "typer",
# ]
# ///

import typer
from gtfparse import read_gtf
from pathlib import Path

app = typer.Typer()

def get_max_transcript_length_per_gene(gtf_file: Path, output_file: Path | None = None):
    """Calculate the maximum transcript length per gene from a GTF file."""
    # Read GTF file and filter for exons
    df = read_gtf(gtf_file)
    exons = df[df['feature'] == 'exon'].copy()
    
    # Calculate exon lengths
    exons['exon_length'] = exons['end'] - exons['start'] + 1
    
    # Group by transcript and sum exon lengths to get transcript lengths
    transcript_lengths = exons.groupby('transcript_id').agg({
        'exon_length': 'sum',
        'gene_id': 'first'
    }).reset_index()
    
    # Find maximum transcript length per gene
    max_lengths = transcript_lengths.groupby('gene_id')['exon_length'].max().reset_index()
    max_lengths.columns = ['gene_id', 'max_transcript_length']
    
    # Sort by gene_id
    max_lengths = max_lengths.sort_values('gene_id')
    
    # Save to file or print to stdout
    if output_file:
        max_lengths.to_csv(output_file, sep='\t', index=False)
        typer.echo(f"Results saved to {output_file}")
    else:
        for _, row in max_lengths.iterrows():
            print(f"{row['gene_id']}\t{row['max_transcript_length']}")

@app.command()
def main(
    gtf_file: Path = typer.Argument(..., help="Path to the GTF file", exists=True),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path to save results as a TSV table")
):
    """
    Calculate the maximum transcript length per gene from a GTF file.
    
    For each gene, this script finds the longest transcript (sum of all exon lengths)
    and outputs the gene ID and maximum transcript length.
    """
    get_max_transcript_length_per_gene(gtf_file, output)

if __name__ == "__main__":
    app()
