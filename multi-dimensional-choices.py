"""Wanted / unwanted two-sided 3-D choice visualization.

Wanted scores extend upward from z=0.  Unwanted risk scores for the same
candidate extend downward from z=0.  The candidate chosen by ``fetch`` is
crimson in both halves; candidates retained by the wanted stage are gold.

Examples
--------
Run with the default 10 candidates and create an interactive HTML file::

    python multi-dimensional-choices.py

Change the number of candidates and keep only the HTML output::

    python multi-dimensional-choices.py --num-elements 150 --no-show
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np


DEFAULT_NUM_ELEMENTS = 10
DEFAULT_COLUMNS = 10

FETCH_COLOR = "crimson"
CONSIDERED_COLOR = "gold"
OTHER_COLOR = "#00ceaa"


def get_keys_by_value(elements: Mapping[int, int], value: int) -> list[int]:
    """Return every candidate whose score equals ``value``."""

    return [key for key, item_value in elements.items() if item_value == value]


def average_squared_distance(values: Iterable[int], center: int) -> float:
    """Average squared distance from ``center``."""

    values = list(values)
    return sum((value - center) ** 2 for value in values) / len(values)


def wanted_threshold(values: Sequence[int]) -> float:
    """Find the original high-wanted cluster threshold.

    For very small demos (fewer than four candidates), all candidates are kept
    so ``num_elements`` remains safely adjustable.
    """

    ordered = sorted(values)
    if len(ordered) < 4 or len(set(ordered)) == 1:
        return float(min(ordered))

    minimum = ordered[0]
    maximum = ordered[-1]
    middle = ordered[1:-1]
    if len(middle) < 2:
        return float(minimum)

    objective: dict[int, float] = {}
    for split in range(len(middle) - 1):
        objective[split] = average_squared_distance(
            middle[: split + 1], minimum
        ) + average_squared_distance(middle[split + 1 :], maximum)

    best_split = min(objective, key=objective.get)
    higher_half = middle[best_split + 1 :]
    return sum(higher_half) / len(higher_half)


def choose_candidate(
    wanted: Mapping[int, int],
    unwanted: Mapping[int, int],
    rng: random.Random,
) -> tuple[int, list[int], float, list[int]]:
    """Apply wanted filtering, then minimize unwanted risk.

    The score is the squared distance from the ideal point
    ``(maximum wanted, zero unwanted)``.  This is equivalent to the intent of
    the original ``penLayers`` calculation, but makes the two-stage mechanism
    explicit and safe for any positive candidate count.
    """

    if not wanted:
        raise ValueError("wanted and unwanted must contain at least one candidate")
    if set(wanted) != set(unwanted):
        raise ValueError("wanted and unwanted must contain the same candidate IDs")

    threshold = wanted_threshold(list(wanted.values()))
    considered = sorted(
        candidate
        for candidate, preference in wanted.items()
        if preference >= threshold
    )
    if not considered:
        considered = get_keys_by_value(wanted, max(wanted.values()))

    maximum_wanted = max(wanted.values())
    distances = {
        candidate: (maximum_wanted - wanted[candidate]) ** 2
        + unwanted[candidate] ** 2
        for candidate in considered
    }
    best_distance = min(distances.values())
    finalists = sorted(
        candidate
        for candidate, distance in distances.items()
        if distance == best_distance
    )
    fetch = rng.choice(finalists)
    return fetch, considered, threshold, finalists


def candidate_colors(
    candidate_ids: Sequence[int], considered: Sequence[int], fetch: int
) -> list[str]:
    """Use the same candidate color in wanted and unwanted."""

    considered_set = set(considered)
    return [
        FETCH_COLOR
        if candidate == fetch
        else CONSIDERED_COLOR
        if candidate in considered_set
        else OTHER_COLOR
        for candidate in candidate_ids
    ]


def plot_combined_matplotlib(
    wanted: Mapping[int, int],
    unwanted: Mapping[int, int],
    considered: Sequence[int],
    fetch: int,
    *,
    columns: int = DEFAULT_COLUMNS,
    png_output: str | Path | None = None,
    show: bool = True,
) -> plt.Figure:
    """Draw one connected chart: wanted up and unwanted down."""

    candidate_ids = sorted(wanted)
    xpos = np.array([index % columns for index in range(len(candidate_ids))])
    ypos = np.array([index // columns for index in range(len(candidate_ids))])
    zeros = np.zeros(len(candidate_ids))
    widths = np.full(len(candidate_ids), 0.82)
    colors = candidate_colors(candidate_ids, considered, fetch)

    wanted_heights = np.array([wanted[candidate] for candidate in candidate_ids])
    risk_heights = np.array([unwanted[candidate] for candidate in candidate_ids])

    figure = plt.figure(figsize=(18.5, 10.5))
    axis = figure.add_subplot(111, projection="3d")
    axis.bar3d(
        xpos,
        ypos,
        zeros,
        widths,
        widths,
        wanted_heights,
        color=colors,
        shade=True,
    )
    axis.bar3d(
        xpos,
        ypos,
        -risk_heights,
        widths,
        widths,
        risk_heights,
        color=colors,
        shade=True,
    )

    # The z=0 surface makes the connection between both dimensions explicit.
    rows = max(ypos) + 1
    plane_x, plane_y = np.meshgrid(
        np.array([-0.2, columns + 0.1]), np.array([-0.2, rows + 0.1])
    )
    axis.plot_surface(
        plane_x,
        plane_y,
        np.zeros_like(plane_x),
        color="#808080",
        alpha=0.12,
        shade=False,
    )

    fetch_position = candidate_ids.index(fetch)
    fetch_x = fetch_position % columns + 0.41
    fetch_y = fetch_position // columns + 0.41
    axis.text(
        fetch_x,
        fetch_y,
        wanted[fetch] + 1,
        f"fetch {fetch}",
        color=FETCH_COLOR,
        ha="center",
    )
    axis.text(
        fetch_x,
        fetch_y,
        -unwanted[fetch] - 2,
        f"risk {unwanted[fetch]}",
        color=FETCH_COLOR,
        ha="center",
    )

    axis.set_title("Wanted (up) / Unwanted risk (down)")
    axis.set_xlabel("candidate column")
    axis.set_ylabel("candidate row")
    axis.set_zlabel("wanted (+) / unwanted risk (-)")
    axis.view_init(elev=24, azim=-56)
    figure.tight_layout()

    if png_output is not None:
        figure.savefig(Path(png_output).expanduser(), dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    return figure


def _cuboid_mesh(
    x0: float, x1: float, y0: float, y1: float, z0: float, z1: float
) -> tuple[list[float], list[float], list[float], list[int], list[int], list[int]]:
    """Return Plotly Mesh3d vertices and triangular faces for one cuboid."""

    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    return x, y, z, i, j, k


def write_interactive_html(
    wanted: Mapping[int, int],
    unwanted: Mapping[int, int],
    considered: Sequence[int],
    fetch: int,
    *,
    columns: int = DEFAULT_COLUMNS,
    html_output: str | Path = "wanted_unwanted_interactive.html",
) -> Path:
    """Write a standalone Plotly HTML chart that can be dragged to rotate."""

    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise RuntimeError(
            "Interactive HTML requires Plotly: python -m pip install plotly"
        ) from exc

    candidate_ids = sorted(wanted)
    colors = candidate_colors(candidate_ids, considered, fetch)
    traces: list[object] = []

    for position, (candidate, color) in enumerate(zip(candidate_ids, colors)):
        x0 = position % columns
        y0 = position // columns
        status = (
            "fetch"
            if candidate == fetch
            else "wanted candidate"
            if candidate in considered
            else "other"
        )

        wx, wy, wz, wi, wj, wk = _cuboid_mesh(
            x0, x0 + 0.82, y0, y0 + 0.82, 0, wanted[candidate]
        )
        ux, uy, uz, ui, uj, uk = _cuboid_mesh(
            x0, x0 + 0.82, y0, y0 + 0.82, -unwanted[candidate], 0
        )
        offset = len(wx)
        hover_wanted = (
            f"candidate {candidate}<br>wanted: {wanted[candidate]}"
            f"<br>unwanted risk: {unwanted[candidate]}<br>{status}"
        )
        hover_unwanted = (
            f"candidate {candidate}<br>unwanted risk: {unwanted[candidate]}"
            f"<br>wanted: {wanted[candidate]}<br>{status}"
        )

        traces.append(
            go.Mesh3d(
                x=wx + ux,
                y=wy + uy,
                z=wz + uz,
                i=wi + [value + offset for value in ui],
                j=wj + [value + offset for value in uj],
                k=wk + [value + offset for value in uk],
                color=color,
                opacity=0.94,
                flatshading=True,
                name=f"candidate {candidate}",
                hovertext=[hover_wanted] * 8 + [hover_unwanted] * 8,
                hovertemplate="%{hovertext}<extra></extra>",
                showscale=False,
                showlegend=False,
            )
        )

    # Legend-only markers keep the meaning clear without duplicating 100 labels.
    for label, color, symbol in (
        (f"fetch: candidate {fetch}", FETCH_COLOR, "diamond"),
        ("wanted-stage candidates", CONSIDERED_COLOR, "square"),
        ("other candidates", OTHER_COLOR, "circle"),
    ):
        traces.append(
            go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode="markers",
                marker={"size": 7, "color": color, "symbol": symbol},
                name=label,
                hoverinfo="skip",
            )
        )

    rows = math.ceil(len(candidate_ids) / columns)
    maximum_extent = max(max(wanted.values()), max(unwanted.values()), 1)
    figure = go.Figure(data=traces)
    figure.update_layout(
        title="Wanted (up) / Unwanted risk (down)",
        scene={
            "dragmode": "orbit",
            "xaxis": {"title": "candidate column", "range": [-0.5, columns + 0.5]},
            "yaxis": {"title": "candidate row", "range": [-0.5, rows + 0.5]},
            "zaxis": {
                "title": "wanted (+) / unwanted risk (-)",
                "range": [-maximum_extent * 1.12, maximum_extent * 1.12],
                "zeroline": True,
                "zerolinewidth": 4,
            },
            "camera": {"eye": {"x": 1.55, "y": -1.55, "z": 1.1}},
            "aspectmode": "manual",
            "aspectratio": {
                "x": 1.35,
                "y": max(0.65, rows / max(columns, 1)),
                "z": 1.25,
            },
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 0, "r": 0, "b": 0, "t": 80},
    )

    output_path = Path(html_output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(
        output_path,
        include_plotlyjs=True,
        full_html=True,
        config={"displaylogo": False, "scrollZoom": True, "responsive": True},
    )
    return output_path


def generate_scores(
    num_elements: int = DEFAULT_NUM_ELEMENTS, *, seed: int | None = None
) -> tuple[dict[int, int], dict[int, int], random.Random]:
    """Generate wanted and unwanted scores for the same candidate IDs."""

    if num_elements < 1:
        raise ValueError("num_elements must be at least 1")
    rng = random.Random(seed)
    wanted = {candidate: rng.randint(0, 50) for candidate in range(num_elements)}
    unwanted = {candidate: rng.randint(0, 50) for candidate in range(num_elements)}
    return wanted, unwanted, rng


def run_demo(
    num_elements: int = DEFAULT_NUM_ELEMENTS,
    *,
    seed: int | None = None,
    columns: int = DEFAULT_COLUMNS,
    html_output: str | Path | None = "wanted_unwanted_interactive.html",
    png_output: str | Path | None = None,
    show: bool = True,
) -> int:
    """Generate data, choose fetch, and render the connected visualization."""

    if columns < 1:
        raise ValueError("columns must be at least 1")

    wanted, unwanted, rng = generate_scores(num_elements, seed=seed)
    fetch, considered, threshold, finalists = choose_candidate(wanted, unwanted, rng)

    print(f"num_elements: {num_elements}")
    print(f"wanted threshold: {threshold:.2f}")
    print(f"wanted-stage candidates: {considered}")
    print(f"finalists: {finalists}")
    print(
        "fetch:",
        fetch,
        "wanted votes:",
        wanted[fetch],
        "/",
        max(wanted.values()),
        "unwanted risk:",
        unwanted[fetch],
        "/",
        max(unwanted.values()),
    )

    if html_output is not None:
        output_path = write_interactive_html(
            wanted,
            unwanted,
            considered,
            fetch,
            columns=columns,
            html_output=html_output,
        )
        print(f"interactive HTML: {output_path}")

    plot_combined_matplotlib(
        wanted,
        unwanted,
        considered,
        fetch,
        columns=columns,
        png_output=png_output,
        show=show,
    )
    return fetch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize wanted upward and unwanted risk downward."
    )
    parser.add_argument(
        "--num-elements",
        type=int,
        default=DEFAULT_NUM_ELEMENTS,
        help=f"number of candidate items (default: {DEFAULT_NUM_ELEMENTS})",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=DEFAULT_COLUMNS,
        help=f"number of grid columns (default: {DEFAULT_COLUMNS})",
    )
    parser.add_argument("--seed", type=int, default=None, help="optional random seed")
    parser.add_argument(
        "--html-output",
        default="wanted_unwanted_interactive.html",
        help="interactive HTML output path",
    )
    parser.add_argument(
        "--no-html", action="store_true", help="do not create interactive HTML"
    )
    parser.add_argument("--png-output", default=None, help="optional PNG output path")
    parser.add_argument(
        "--no-show", action="store_true", help="do not open the Matplotlib window"
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_demo(
        num_elements=arguments.num_elements,
        seed=arguments.seed,
        columns=arguments.columns,
        html_output=None if arguments.no_html else arguments.html_output,
        png_output=arguments.png_output,
        show=not arguments.no_show,
    )
