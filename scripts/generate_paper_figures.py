#!/usr/bin/env python3
"""Generate publication-ready figures for the Complex Networks 2026 paper.

Uses the EDEL dashboard figure generation engine to produce high-resolution
vector PDF and PNG figures for the benchmark experiments across Featherweight_OCL,
HOL-Library, AVL-Trees, and Aho_Corasick.

Figures generated:
1. fig_simplex_const_subst.{pdf,png} - Intrinsic 3D Epistemic Simplex for const_subst
2. fig_joint_simplices.{pdf,png} - Joint 3D PCA projection of target & bridge simplices
3. fig_transition_neighborhood_const_subst.{pdf,png} - Transition Neighborhood D(M|p)
4. fig_landscape_terrain_2d.{pdf,png} - 2D Landscape Height (H) contour map
5. fig_landscape_terrain_3d.{pdf,png} - 3D Landscape Height (H) surface elevation map
6. latex_snippets.tex - Ready-to-use LaTeX figure environments
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from edel.experiments.registry import init_registry, get_experiment
from edel.io.artifact import make_stage_artifact, load_artifact
from edel.dashboard.callbacks.paper_figures import (
    _build_fig_h1_simplex,
    _build_fig_h2_neighborhoods,
    _build_fig_h2_connected_3d,
    apply_paper_style,
)
from edel.viz.landscape import plot_landscape_3d, plot_landscape_contour

def main():
    base_path = Path("artifacts")
    output_dir = Path("complex_networks_paper/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    init_registry(base_path / "configs")
    config = get_experiment("afp_lemma")
    
    print("=" * 75)
    print("Generating publication-ready figures for the benchmark experiments...")
    print("=" * 75)
    
    # 1. Load benchmark dataset (1,924 lemmas)
    clust_art = make_stage_artifact(config, base_path, "clustering", "clustering")
    df = load_artifact(clust_art)
    print(f"Loaded benchmark dataset with {len(df)} items.")
    
    land_art = make_stage_artifact(config, base_path, "output", "landscape_results")
    landscape_results = load_artifact(land_art)
    print(f"Loaded landscape terrain results: {list(landscape_results.keys())}")
    
    font = "Times New Roman"
    base_font_size = 13
    style_opts = ["paper-style", "gridlines"]
    
    # Identify target case study theorems
    target_id = "Featherweight_OCL.UML_Logic.const_subst"
    bridge_ids = [
        "Featherweight_OCL.UML_Logic.cp_OclIf",
        "Featherweight_OCL.UML_Logic.cp_OclNot",
    ]
    multiset_matches = df[df["title"].str.contains("mset_le_incr_right|Multiset.diff_add", na=False)]
    multiset_id = multiset_matches.iloc[0]["id"] if not multiset_matches.empty else "HOL-Library.Multiset.mset_le_incr_right"
    
    latex_snippets = []

    # -----------------------------------------------------------------------
    # Figure 1: Single 3D Intrinsic Simplex (const_subst)
    # -----------------------------------------------------------------------
    print(f"\n[Figure 1] Building Intrinsic 3D Simplex for '{target_id}'...")
    fig1, cap1, _ = _build_fig_h1_simplex(
        df=df,
        exp_name="afp_lemma",
        paper_ids=target_id,
        font=font,
        base_font_size=base_font_size,
        style_opts=style_opts,
        base_path=base_path
    )
    fig1.update_layout(
        title="",  # Title in LaTeX caption
        margin=dict(l=20, r=20, t=20, b=20),
        scene=dict(
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
        )
    )
    
    out_pdf1 = output_dir / "fig_simplex_const_subst.pdf"
    out_png1 = output_dir / "fig_simplex_const_subst.png"
    pio.write_image(fig1, str(out_pdf1), width=900, height=700)
    pio.write_image(fig1, str(out_png1), width=1800, height=1400, scale=2)
    print(f"  Exported -> {out_pdf1}")
    print(f"  Exported -> {out_png1}")
    
    latex_snippets.append(r"""
\begin{figure}[t!]
\centering
\includegraphics[width=0.72\textwidth]{figures/fig_simplex_const_subst.pdf}
\caption{Intrinsic epistemic 3-simplex $\sigma_j$ for theorem \texttt{Featherweight\_OCL.UML\_Logic.const\_subst}. Classical MDS preserves all six pairwise Euclidean distances between the four aspect embeddings ($\mathbf{p}, \mathbf{m}, \mathbf{f}, \mathbf{i}$). The sequential trajectory $P \to M \to F \to I$ is highlighted in solid gold, while non-adjacent tetrahedron edges are rendered dashed, demonstrating a non-degenerate spatial volume.}
\label{fig:simplex_const_subst}
\end{figure}
""".strip())

    # -----------------------------------------------------------------------
    # Figure 2: Joint 3D Simplicial Complex Projection
    # -----------------------------------------------------------------------
    joint_ids = [target_id] + bridge_ids + [multiset_id]
    print(f"\n[Figure 2] Building Joint 3D Simplices Projection for {len(joint_ids)} theorems...")
    fig2, cap2, _ = _build_fig_h1_simplex(
        df=df,
        exp_name="afp_lemma",
        paper_ids=joint_ids,
        font=font,
        base_font_size=base_font_size,
        style_opts=style_opts,
        base_path=base_path
    )
    fig2.update_layout(
        title="",
        margin=dict(l=20, r=280, t=20, b=20),
        scene=dict(
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.3))
        )
    )
    
    out_pdf2 = output_dir / "fig_joint_simplices.pdf"
    out_png2 = output_dir / "fig_joint_simplices.png"
    pio.write_image(fig2, str(out_pdf2), width=1100, height=750)
    pio.write_image(fig2, str(out_png2), width=2200, height=1500, scale=2)
    print(f"  Exported -> {out_pdf2}")
    print(f"  Exported -> {out_png2}")
    
    latex_snippets.append(r"""
\begin{figure}[t!]
\centering
\includegraphics[width=0.85\textwidth]{figures/fig_joint_simplices.pdf}
\caption{Joint 3D PCA projection of epistemic 3-simplices across benchmark theorems. Target theorem \texttt{const\_subst} is projected alongside parent theory bridge lemmas (\texttt{cp\_OclIf}, \texttt{cp\_OclNot}) and foundational algebra lemma \texttt{Multiset.mset\_le\_incr\_right}. Distinct trajectory geometries reflect domain-specific proof strategies.}
\label{fig:joint_simplices}
\end{figure}
""".strip())

    # -----------------------------------------------------------------------
    # Figure 3: Transition Neighborhood D(M | p)
    # -----------------------------------------------------------------------
    print(f"\n[Figure 3] Building Transition Neighborhood D(M|p) for '{target_id}'...")
    fig3, cap3, _ = _build_fig_h2_neighborhoods(
        df=df,
        exp_name="afp_lemma",
        paper_id=target_id,
        transition="pm",
        k_neighbors=5,
        font=font,
        base_font_size=base_font_size,
        style_opts=style_opts,
        base_path=base_path,
        custom_exp_name="AFP Benchmark"
    )
    fig3.update_layout(title="", margin=dict(l=45, r=30, t=20, b=45))
    
    out_pdf3 = output_dir / "fig_transition_neighborhood_const_subst.pdf"
    out_png3 = output_dir / "fig_transition_neighborhood_const_subst.png"
    pio.write_image(fig3, str(out_pdf3), width=900, height=650)
    pio.write_image(fig3, str(out_png3), width=1800, height=1300, scale=2)
    print(f"  Exported -> {out_pdf3}")
    print(f"  Exported -> {out_png3}")
    
    latex_snippets.append(r"""
\begin{figure}[t!]
\centering
\includegraphics[width=0.72\textwidth]{figures/fig_transition_neighborhood_const_subst.pdf}
\caption{Strategic transition neighborhood $D(M \mid p)$ for theorem \texttt{const\_subst} ($k=5$ neighbors). In contrast to flat retrieval which is dominated by superficial lexical overlap, higher-order transition mapping directs search from premise representations directly into proof strategy space ($M$), retrieving parent bridge lemmas.}
\label{fig:transition_neighborhood}
\end{figure}
""".strip())

    # -----------------------------------------------------------------------
    # Figure 4: 2D Epistemic Landscape Contour (Height H)
    # -----------------------------------------------------------------------
    print("\n[Figure 4] Building 2D Landscape Height (H) Contour Map...")
    fig4 = plot_landscape_contour(
        df=df,
        landscape_results=landscape_results,
        method="diffusion",
        color_col="cluster_domain",
        title="",
        z_label="Reachability Height log10(1+H)",
        show_regions=True,
        show_frontier=False,
        show_papers=True,
        top_papers_n=8,
        papers_metric="cluster_centroids",
        show_flow=False
    )
    apply_paper_style(fig4, font, True, style_opts, base_font_size)
    fig4.update_layout(
        title="",
        margin=dict(l=75, r=35, t=25, b=65),
        xaxis=dict(
            range=[-0.05, 0.06],
            title=dict(
                text="Diffusion Coordinate 1 (Premise Space)",
                font=dict(family=font, size=18, color="black")
            ),
            tickfont=dict(family=font, size=15, color="black"),
            linecolor="black",
            linewidth=1.2,
            mirror=True,
            ticks="outside"
        ),
        yaxis=dict(
            range=[0.06, -0.05],
            title=dict(
                text="Diffusion Coordinate 2 (Premise Space)",
                font=dict(family=font, size=18, color="black")
            ),
            tickfont=dict(family=font, size=15, color="black"),
            linecolor="black",
            linewidth=1.2,
            mirror=True,
            ticks="outside"
        ),
        legend=dict(
            font=dict(family=font, size=15, color="black"),
            title=dict(font=dict(family=font, size=16, color="black")),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="black",
            borderwidth=1.2,
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top"
        )
    )
    
    out_pdf4 = output_dir / "fig_landscape_terrain_2d.pdf"
    out_png4 = output_dir / "fig_landscape_terrain_2d.png"
    pio.write_image(fig4, str(out_pdf4), width=1150, height=650)
    pio.write_image(fig4, str(out_png4), width=2300, height=1300, scale=2)
    print(f"  Exported -> {out_pdf4}")
    print(f"  Exported -> {out_png4}")
    
    latex_snippets.append(r"""
\begin{figure}[t!]
\centering
\includegraphics[width=0.92\textwidth]{figures/fig_landscape_terrain_2d.pdf}
\caption{2D Epistemic Landscape Height ($H$) contour terrain across the benchmark theorems after removing the top 10 syntactic principal components, clipped to the primary operational manifold $\psi_1, \psi_2 \in [-0.05, 0.06]$ to isolate core deductive topology from peripheral syntax outliers. Elevation contours denote downstream reachability cone size $\log_{10}(1+H(v))$. Foundational algebraic hubs (e.g., \texttt{true}, \texttt{false}, \texttt{StrongEq}) anchor dense reachability basins, while dashed boundaries trace the domain regions of the four benchmark theories shown on the map (\texttt{HOL-Library}, \texttt{Featherweight\_OCL}, \texttt{AVL-Trees}, and \texttt{Aho\_Corasick}).}
\label{fig:landscape_terrain_2d}
\end{figure}
""".strip())

    # -----------------------------------------------------------------------
    # Figure 5: 3D Epistemic Landscape Surface (Height H)
    # -----------------------------------------------------------------------
    print("\n[Figure 5] Building 3D Landscape Height Surface Map...")
    fig5 = plot_landscape_3d(
        df=df,
        landscape_results=landscape_results,
        method="diffusion",
        color_col="cluster_domain",
        title="",
        show_papers=True,
        top_papers_n=8,
        papers_metric="cited_by_count"
    )
    apply_paper_style(fig5, font, True, style_opts, base_font_size)
    fig5.update_layout(
        title="",
        margin=dict(l=10, r=10, t=10, b=10),
        scene=dict(
            xaxis_title="Diffusion 1",
            yaxis_title="Diffusion 2",
            zaxis_title="Landscape Height log(1+H)",
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.3))
        )
    )
    
    out_pdf5 = output_dir / "fig_landscape_terrain_3d.pdf"
    out_png5 = output_dir / "fig_landscape_terrain_3d.png"
    pio.write_image(fig5, str(out_pdf5), width=1000, height=800)
    pio.write_image(fig5, str(out_png5), width=2000, height=1600, scale=2)
    print(f"  Exported -> {out_pdf5}")
    print(f"  Exported -> {out_png5}")
    
    latex_snippets.append(r"""
\begin{figure}[t!]
\centering
\includegraphics[width=0.82\textwidth]{figures/fig_landscape_terrain_3d.pdf}
\caption{3D continuous Epistemic Landscape over the Isabelle/HOL benchmark corpus. Topographic peaks correspond to core deductive anchors with large transitive dependency cones, guiding multi-agent reasoning toward structurally sound proof steps.}
\label{fig:landscape_terrain_3d}
\end{figure}
""".strip())

    # Write LaTeX snippets file
    out_snippets = output_dir / "latex_snippets.tex"
    with out_snippets.open("w", encoding="utf-8") as f:
        f.write("% Auto-generated LaTeX figure snippets for Complex Networks 2026 paper\n\n")
        f.write("\n\n% " + "=" * 60 + "\n\n".join(latex_snippets))
        f.write("\n")
    print(f"\n[LaTeX] Wrote figure snippets -> {out_snippets}")

    print("\n" + "=" * 75)
    print("All paper figures successfully generated and saved to complex_networks_paper/figures/!")
    print("=" * 75)

if __name__ == "__main__":
    main()
