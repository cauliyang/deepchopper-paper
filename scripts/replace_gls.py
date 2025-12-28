# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "typer>=0.9.0",
#     "rich>=13.0.0",
# ]
# ///

r"""CLI tool to replace LaTeX \gls commands with plain text.

This tool parses \newacronym definitions and replaces \gls{} commands
with their text equivalents based on the selected mode.
"""

import re
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="Replace LaTeX \\gls commands with plain text",
    add_completion=False,
)
console = Console()


class ReplacementMode(str, Enum):
    """Replacement mode for glossary terms."""

    short = "short"
    long = "long"
    both = "both"


class GlossaryReplacer:
    def __init__(self):
        self.acronyms: dict[str, tuple[str, str]] = {}  # {key: (short, long)}
        self.first_use: set[str] = set()  # Track first use of acronyms

    def parse_acronyms(self, content: str) -> None:
        """Parse \newacronym definitions from LaTeX content."""
        # Pattern: \newacronym{key}{short}{long}
        pattern = r"\\newacronym\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}"

        for match in re.finditer(pattern, content):
            key = match.group(1)
            short = match.group(2)
            long = match.group(3)
            self.acronyms[key] = (short, long)

    def replace_gls(
        self,
        content: str,
        mode: ReplacementMode = ReplacementMode.short,
        first_use_expand: bool = False,
    ) -> str:
        r"""Replace \gls commands with plain text.

        Args:
            content: LaTeX content
            mode: Replacement mode - 'short', 'long', or 'both'
            first_use_expand: If True, expand on first use (mode is ignored for first use)

        Returns:
            Modified content with \gls commands replaced
        """

        def replace_match(match):
            # Extract command and key
            command = match.group(1)  # 'gls' or 'Gls' etc.
            key = match.group(2)

            if key not in self.acronyms:
                # Unknown acronym, keep original
                return match.group(0)

            short, long = self.acronyms[key]

            # Determine replacement text
            if first_use_expand and key not in self.first_use:
                # First use: expand as "long (short)"
                replacement = f"{long} ({short})"
                self.first_use.add(key)
            else:
                # Subsequent uses or non-first-use mode
                if mode == ReplacementMode.short:
                    replacement = short
                elif mode == ReplacementMode.long:
                    replacement = long
                elif mode == ReplacementMode.both:
                    replacement = f"{long} ({short})"
                else:
                    replacement = short

            # Handle capitalization
            if command == "Gls":
                replacement = (
                    replacement[0].upper() + replacement[1:]
                    if replacement
                    else replacement
                )

            return replacement

        # Pattern: \gls{key} or \Gls{key}
        pattern = r"\\(gls|Gls)\{([^}]+)\}"

        return re.sub(pattern, replace_match, content)

    def process_file(
        self,
        input_file: Path,
        output_file: Path | None = None,
        mode: ReplacementMode = ReplacementMode.short,
        first_use_expand: bool = False,
        in_place: bool = False,
    ) -> str:
        """Process a LaTeX file and replace \gls commands.

        Args:
            input_file: Path to input LaTeX file
            output_file: Path to output file (None for stdout)
            mode: Replacement mode
            first_use_expand: Expand on first use
            in_place: Modify file in place

        Returns:
            Processed content
        """
        # Read input file
        content = input_file.read_text(encoding="utf-8")

        # Parse acronyms first
        self.parse_acronyms(content)

        # Replace \gls commands
        result = self.replace_gls(content, mode, first_use_expand)

        # Output handling
        if in_place:
            input_file.write_text(result, encoding="utf-8")
        elif output_file:
            output_file.write_text(result, encoding="utf-8")

        return result


@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        help="Input LaTeX file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (default: stdout)",
    ),
    in_place: bool = typer.Option(
        False,
        "--in-place",
        "-i",
        help="Modify file in place",
    ),
    mode: ReplacementMode = typer.Option(
        ReplacementMode.short,
        "--mode",
        "-m",
        help="Replacement mode",
        case_sensitive=False,
    ),
    first_use: bool = typer.Option(
        False,
        "--first-use",
        "-f",
        help='Expand on first use as "long (short)", then use short form',
    ),
    list_acronyms: bool = typer.Option(
        False,
        "--list-acronyms",
        "-l",
        help="List all acronyms and exit",
    ),
):
    """
    Replace LaTeX \\gls commands with plain text.

    Examples:

    \b
    # Replace with short forms (default)
    replace-gls main.tex

    \b
    # Replace with long forms
    replace-gls main.tex --mode long

    \b
    # Replace with "long (short)" format
    replace-gls main.tex --mode both

    \b
    # Expand on first use, short on subsequent uses
    replace-gls main.tex --first-use

    \b
    # Save to output file
    replace-gls main.tex -o output.tex

    \b
    # Modify file in place
    replace-gls main.tex --in-place

    \b
    # List all acronyms defined in the file
    replace-gls main.tex --list-acronyms
    """
    # Create replacer
    replacer = GlossaryReplacer()

    # If list mode, just parse and display acronyms
    if list_acronyms:
        content = input_file.read_text(encoding="utf-8")
        replacer.parse_acronyms(content)

        table = Table(title=f"Found {len(replacer.acronyms)} acronyms")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Short", style="magenta")
        table.add_column("Long", style="green")

        for key, (short, long) in sorted(replacer.acronyms.items()):
            table.add_row(key, short, long)

        console.print(table)
        return

    # Process file
    result = replacer.process_file(input_file, output, mode, first_use, in_place)

    # Print to stdout if no output file specified and not in-place
    if not output and not in_place:
        console.print(result)

    # Print success message for file operations
    if in_place:
        console.print(
            f"[green]✓[/green] Successfully modified '{input_file}' in place", err=True
        )
    elif output:
        console.print(
            f"[green]✓[/green] Successfully wrote output to '{output}'", err=True
        )


if __name__ == "__main__":
    app()
