# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "typer>=0.9.0",
#     "rich>=13.0.0",
# ]
# ///

r"""CLI tool to neutralize LaTeX commands by replacing them with plain text.

Features:
- Replace \gls commands with plain text
- Resolve \ref commands to actual figure/table numbers
"""

import re
import sys
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="Neutralize LaTeX commands by replacing with plain text",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
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

    def pluralize(self, text: str) -> str:
        """Simple pluralization of English words."""
        if not text:
            return text

        # Handle common cases
        text = text.strip()
        lower_text = text.lower()

        # Special cases
        if lower_text.endswith(("s", "x", "z", "ch", "sh")):
            return f"{text}es"
        elif lower_text.endswith("y") and len(text) > 1 and text[-2] not in "aeiou":
            return f"{text[:-1]}ies"
        elif lower_text.endswith("f"):
            return f"{text[:-1]}ves"
        elif lower_text.endswith("fe"):
            return f"{text[:-2]}ves"
        else:
            return f"{text}s"

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

        Supports:
        - \gls{key} - basic reference
        - \Gls{key} - capitalized
        - \glspl{key} - plural
        - \Glspl{key} - capitalized plural
        - \acrshort{key} - short form
        - \acrlong{key} - long form
        - \acrfull{key} - full form (long (short))

        Args:
            content: LaTeX content
            mode: Replacement mode - 'short', 'long', or 'both'
            first_use_expand: If True, expand on first use (mode is ignored for first use)

        Returns:
            Modified content with \gls commands replaced
        """

        def replace_match(match):
            # Extract command and key
            command = match.group(1)  # 'gls', 'Gls', 'glspl', etc.
            key = match.group(2)

            if key not in self.acronyms:
                # Unknown acronym, keep original
                return match.group(0)

            short, long = self.acronyms[key]

            # Determine base replacement text based on command type
            if command in ("acrshort",):
                replacement = short
            elif command in ("acrlong",):
                replacement = long
            elif command in ("acrfull",):
                replacement = f"{long} ({short})"
            elif first_use_expand and key not in self.first_use:
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

            # Handle pluralization for \glspl and \Glspl
            if command.lower() in ("glspl",):
                # For "both" mode with plural, pluralize the short form
                if "(" in replacement and ")" in replacement:
                    # Format: "long (short)" -> "longs (shorts)"
                    parts = replacement.split("(")
                    long_part = parts[0].strip()
                    short_part = parts[1].rstrip(")")
                    replacement = (
                        f"{self.pluralize(long_part)} ({self.pluralize(short_part)})"
                    )
                else:
                    replacement = self.pluralize(replacement)

            # Handle capitalization
            if command in ("Gls", "Glspl"):
                replacement = (
                    replacement[0].upper() + replacement[1:]
                    if replacement
                    else replacement
                )

            return replacement

        # Pattern: match all gls variants
        # Matches: \gls, \Gls, \glspl, \Glspl, \acrshort, \acrlong, \acrfull
        pattern = r"\\(gls|Gls|glspl|Glspl|acrshort|acrlong|acrfull)\{([^}]+)\}"

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


class ReferenceResolver:
    def __init__(self):
        self.labels: dict[str, str] = {}  # {label: number}

    def parse_aux_file(self, aux_file: Path) -> None:
        """Parse a .aux file to extract label-to-number mappings.

        Format: \\newlabel{label}{{number}{page}{caption}{internal}{}}
        Example: \\newlabel{fig:f1}{{1}{23}{...}{figure.1}{}}
        """
        if not aux_file.exists():
            print(f"Warning: .aux file not found: {aux_file}", file=sys.stderr)
            return

        content = aux_file.read_text(encoding='utf-8')

        # Pattern to match \newlabel{label}{{number}{...}...}
        pattern = r'\\newlabel\{([^}]+)\}\{\{([^}]+)\}'

        for match in re.finditer(pattern, content):
            label = match.group(1)
            number = match.group(2)
            self.labels[label] = number

    def resolve_refs(self, content: str) -> str:
        """Replace \\ref{label} commands with actual numbers.

        Supports:
        - \\ref{label}
        - \\ref{label} (with external references from xr package)
        """
        def replace_match(match):
            label = match.group(1)

            if label not in self.labels:
                # Unknown label (likely internal ref), keep original without warning
                return match.group(0)

            return self.labels[label]

        # Pattern: \ref{label}
        pattern = r'\\ref\{([^}]+)\}'

        return re.sub(pattern, replace_match, content)

    def process_file(
        self,
        input_file: Path,
        output_file: Path | None = None,
        aux_files: list[Path] | None = None,
        in_place: bool = False,
    ) -> str:
        """Process a LaTeX file and replace \\ref commands with numbers.

        Args:
            input_file: Path to input LaTeX file
            output_file: Path to output file (None for stdout)
            aux_files: List of .aux files to parse (default: input file's .aux)
            in_place: Modify file in place

        Returns:
            Processed content
        """
        # Read input file
        content = input_file.read_text(encoding='utf-8')

        # Determine which .aux files to parse
        if aux_files is None:
            # Default: use the input file's .aux file
            aux_files = [input_file.with_suffix('.aux')]

        # Parse all .aux files
        for aux_file in aux_files:
            self.parse_aux_file(aux_file)

        # Replace \ref commands
        result = self.resolve_refs(content)

        # Output handling
        if in_place:
            input_file.write_text(result, encoding='utf-8')
        elif output_file:
            output_file.write_text(result, encoding='utf-8')

        return result


@app.command(name="replace-gls")
def replace_gls_command(
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

    Supports: \\gls, \\Gls, \\glspl, \\Glspl, \\acrshort, \\acrlong, \\acrfull

    Examples:

    \b
    # Replace with short forms (default)
    uv run neutralize.py main.tex

    \b
    # Replace with long forms
    uv run neutralize.py main.tex --mode long

    \b
    # Replace with "long (short)" format
    uv run neutralize.py main.tex --mode both

    \b
    # Expand on first use, short on subsequent uses
    uv run neutralize.py main.tex --first-use

    \b
    # Save to output file
    uv run neutralize.py main.tex -o output.tex

    \b
    # Modify file in place
    uv run neutralize.py main.tex --in-place

    \b
    # List all acronyms defined in the file
    uv run neutralize.py main.tex --list-acronyms
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
        # Use print() instead of console.print() to avoid Rich markup interpretation
        # which would strip LaTeX square brackets like \hyperref[sec:methods]{...}
        print(result)

    # Print success message for file operations
    if in_place:
        console.print(
            f"[green]✓[/green] Successfully modified '{input_file}' in place",
            file=sys.stderr
        )
    elif output:
        console.print(
            f"[green]✓[/green] Successfully wrote output to '{output}'",
            file=sys.stderr
        )


@app.command(name="resolve-refs")
def resolve_refs_command(
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
    aux_files: list[Path] = typer.Option(
        None,
        "--aux",
        "-a",
        help="External .aux files to parse (e.g., from xr package)",
    ),
    include_internal: bool = typer.Option(
        False,
        "--include-internal",
        help="Also replace internal references (from input file's own .aux)",
    ),
    list_labels: bool = typer.Option(
        False,
        "--list-labels",
        "-l",
        help="List all labels and exit",
    ),
):
    """
    Resolve LaTeX \\ref commands to actual figure/table numbers.

    By default, ONLY replaces external references (from xr package) and keeps
    internal references unchanged. Use --include-internal to also replace
    internal references.

    Examples:

    \b
    # Replace ONLY external refs from supplement.aux (internal refs unchanged)
    uv run neutralize.py resolve-refs main.tex --aux supplement.aux

    \b
    # Multiple external aux files
    uv run neutralize.py resolve-refs main.tex -a supplement.aux -a appendix.aux

    \b
    # Also replace internal references
    uv run neutralize.py resolve-refs main.tex --aux supplement.aux --include-internal

    \b
    # Save to output file
    uv run neutralize.py resolve-refs main.tex --aux supplement.aux -o output.tex

    \b
    # List all external labels
    uv run neutralize.py resolve-refs main.tex --aux supplement.aux --list-labels
    """
    # Create resolver
    resolver = ReferenceResolver()

    # Prepare aux file list - by default, ONLY external aux files
    aux_file_list = []

    # Add internal aux file only if requested
    if include_internal:
        aux_file_list.append(input_file.with_suffix('.aux'))

    # Add external aux files
    if aux_files:
        aux_file_list.extend(aux_files)

    # Parse aux files
    for aux_file in aux_file_list:
        resolver.parse_aux_file(aux_file)

    # If list mode, display labels and exit
    if list_labels:
        table = Table(title=f"Found {len(resolver.labels)} labels")
        table.add_column("Label", style="cyan", no_wrap=True)
        table.add_column("Number", style="magenta")

        for label, number in sorted(resolver.labels.items()):
            table.add_row(label, number)

        console.print(table)
        return

    # Process file
    result = resolver.process_file(
        input_file, output, aux_file_list, in_place
    )

    # Print to stdout if no output file specified and not in-place
    if not output and not in_place:
        print(result)

    # Print success message for file operations
    if in_place:
        console.print(
            f"[green]✓[/green] Successfully modified '{input_file}' in place",
            file=sys.stderr
        )
    elif output:
        console.print(
            f"[green]✓[/green] Successfully wrote output to '{output}'",
            file=sys.stderr
        )


if __name__ == "__main__":
    app()
