import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib

def _plot_track_style(
    ax,
    line_seq,
    line_qual,
    line_start,
    adapter_regions,
    y_offset,
    letter_spacing,
    base_width,
    base_height,
    sm,
    qmin,
    qmax,
    is_in_adapter,
    font_size,
):
    """Track style with sequence above and quality track below."""
    seq_y = -y_offset
    qual_y = -y_offset - 0.85

    # Quality track as continuous area
    for j, (base, q) in enumerate(zip(line_seq, line_qual)):
        idx = line_start + j
        x_center = j * letter_spacing
        in_adapter = is_in_adapter(idx)

        # Quality bar
        bar_height = 0.5 * (q - qmin) / (qmax - qmin) if qmax > qmin else 0.25
        rect_color = sm.to_rgba(q)
        bar = Rectangle(
            (x_center - base_width / 2, qual_y),
            width=base_width,
            height=bar_height,
            facecolor=rect_color,
            edgecolor="#CCCCCC",
            linewidth=0.1,
            alpha=0.85,
            zorder=1,
        )
        ax.add_patch(bar)

        # Letter background (subtle)
        bg = Rectangle(
            (x_center - base_width / 2, seq_y - base_height / 2),
            width=base_width,
            height=base_height,
            facecolor=rect_color,
            edgecolor="#CCCCCC",
            linewidth=0.3,
            alpha=0.25,
            zorder=1,
        )
        ax.add_patch(bg)

        # Place the text in the exact center of the background rectangle,
        # corrected for text vertical alignment issues
        # For Nature Methods, consider using a distinct blue for adapters (works well with scientific and Nature color palettes)
        ax.text(
            x_center,
            seq_y - base_height / 16,  # shift text downward to center more precisely
            base,
            fontsize=font_size,
            color="#D62728" if in_adapter else "black",  # blue for adapter regions, black otherwise
            ha="center",
            va="center",
            family="monospace",
            zorder=10,
        )


def plot_sequence_with_quality(
    sequence,
    quality,
    adapter_regions,
    wrap=None,
    ax=None,
    cmap="cividis",
    letter_spacing=0.8,
    dpi=300,
    BASE_FONT_SIZE = 8,
    BASE_WIDTH_RATIO = 1,
    BASE_HEIGHT_RATIO = 0.60,
    show_position=True,
):
    """
    Publication-quality visualization of nucleotide sequences with per-base quality scores.

    Track style shows sequence above with quality bars below, designed for Nature Methods.
    Position indicators show start and end positions on the left and right of each line.

    Args:
        sequence (str): The nucleotide sequence.
        quality (list or np.ndarray): Per-base Phred quality scores.
        adapter_regions (list of tuples): List of (start, end) adapter regions [start, end).
        wrap (int): Bases per line (default: 50).
        ax (matplotlib.Axes or None): Matplotlib Axes to plot on.
        cmap (str): Colormap - 'cividis' (colorblind-safe) or 'viridis'.
        letter_spacing (float): Spacing multiplier between bases.
        dpi (int): Resolution for export (300+ for publication).
        show_position (bool): If True, show start and end positions for each line (default: True).

    Returns:
        matplotlib.figure.Figure, matplotlib.axes.Axes
    """
    # Publication mode settings (always enabled)
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "figure.dpi": dpi,
            "savefig.dpi": dpi,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,  # TrueType fonts (required by Nature)
            "ps.fonttype": 42,
        }
    )

    if wrap is None:
        wrap = determine_wrap_len(sequence)
        print(f"Wrap length: {wrap}")

    # Constants for clean layout
    def is_in_adapter(idx):
        return any(start <= idx < end for start, end in adapter_regions)

    sequence = str(sequence)
    quality = np.array(quality, dtype=float)
    n = len(sequence)
    assert len(quality) == n, (
        f"Quality array length ({len(quality)}) must match sequence length ({n})"
    )

    # Calculate layout for track style
    line_height = 1.5
    n_lines = (n + wrap - 1) // wrap

    # Calculate space needed for position labels (range style: start and end positions)
    pos_label_width = 0
    pos_label_width_right = 0
    if show_position:
        max_pos = n - 1
        # Need space for start and end positions on both sides
        pos_label_width = len(str(max_pos)) * 0.15 + 0.4  # Left side
        pos_label_width_right = len(str(max_pos)) * 0.15 + 0.5  # Right side

    # Figure sizing for Nature Methods (mm to inches)
    if ax is None:
        # Single column: 89mm ≈ 3.5", double column: 183mm ≈ 7.2"
        fig_width = min(7.2, wrap * 0.12 * letter_spacing + pos_label_width + pos_label_width_right)
        fig_height = n_lines * line_height * 0.28
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    else:
        fig = ax.figure

    ax.set_axis_off()

    # Quality normalization with better range handling
    qmin, qmax = np.percentile(quality, [2, 98])  # Robust to outliers
    qrange = qmax - qmin
    if qrange < 1:
        qmin, qmax = quality.min(), quality.max()
        qrange = qmax - qmin if qmax > qmin else 1

    norm = plt.Normalize(qmin, qmax)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)

    y_offset = 0.5
    base_width = BASE_WIDTH_RATIO * letter_spacing
    base_height = BASE_HEIGHT_RATIO

    for i in range(n_lines):
        line_start = i * wrap
        line_end = min((i + 1) * wrap, n)
        line_seq = sequence[line_start:line_end]
        line_qual = quality[line_start:line_end]
        seq_y = -y_offset

        # Draw position indicators (range style: start and end positions)
        if show_position:
            # Start position on left
            ax.text(
                -pos_label_width,
                seq_y - base_height / 16,
                f"{line_start + 1}",
                fontsize=BASE_FONT_SIZE - 2,
                color="gray",
                ha="right",
                va="center",
                family="monospace",
                zorder=10,
            )
            # End position on right - positioned at the end of the sequence
            end_x = (len(line_seq) - 1) * letter_spacing
            ax.text(
                end_x + 0.6,  # Small gap after last base
                seq_y - base_height / 16,
                f"{line_end}",
                fontsize=BASE_FONT_SIZE - 2,
                color="gray",
                ha="left",
                va="center",
                family="monospace",
                zorder=10,
            )

        _plot_track_style(
            ax,
            line_seq,
            line_qual,
            line_start,
            adapter_regions,
            y_offset,
            letter_spacing,
            base_width,
            base_height,
            sm,
            qmin,
            qmax,
            is_in_adapter,
            BASE_FONT_SIZE,
        )

        y_offset += line_height * 1.05  # Tight row spacing

    # Set limits with proper padding
    max_line_length = min(wrap, n)
    x_min = -pos_label_width - 0.2 if show_position and pos_label_width > 0 else -0.5
    # Add space on right for end position
    x_max = max_line_length * letter_spacing - 0.5
    if show_position:
        x_max = max_line_length * letter_spacing + pos_label_width_right
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-y_offset + 0.3, 0.8)  # Compact layout

    # Publication-quality colorbar
    cb = fig.colorbar(
        sm, ax=ax, orientation="vertical", fraction=0.04, pad=0.02, aspect=20
    )
    cb.set_label("Base quality (Q score)", fontsize=BASE_FONT_SIZE + 1, labelpad=8)
    cb.ax.tick_params(labelsize=BASE_FONT_SIZE - 1, width=0.5, length=3)
    cb.outline.set_linewidth(0.5)

    fig.tight_layout()
    return fig, ax

def determine_wrap_len(sequence):
    """Determine the wrap length for the sequence.

    So that the sequence can be wrapped like a square.
    """
    return int(np.sqrt(len(sequence) * 2))


if __name__ == "__main__":
    # Example usage
    sequence = "ATGCGATACGTTACGATCGATCGATAGCTGACGATGGGGGGGAATCGAAAAAATCGGGGG" * 2
    quality = np.random.randint(0, 60, size=len(sequence))
    adapter_regions = [(40, 60)]

    fig, ax = plot_sequence_with_quality(
        sequence,
        quality,
        adapter_regions,
        # wrap=50,
        cmap="cividis",
        dpi=300,
    )
    plt.savefig("vis_seq_qual.pdf", dpi=300)
