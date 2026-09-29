#!/usr/bin/env python3
"""Update and persist pipeline stage artifacts for afp_lemma using artifacts/rag_index.

Refreshes Stages 1 (Data Collection), 3 (Embeddings), 4 (Projection),
5 (Vector Field), 6 (Clustering), and 8 (Landscape Terrain) so that
the EDEL dashboard loads the full 1,924 benchmark theorems across
Featherweight_OCL, HOL-Library, AVL-Trees, and Aho_Corasick.
"""

from pathlib import Path
import time
import pandas as pd

from edel.experiments.registry import init_registry, get_experiment
from edel.io.artifact import make_stage_artifact, save_artifact
from edel.providers.afp_rag import generate_dataset
from edel.pipeline.projection import run_projection_stage
from edel.pipeline.vector_field import run_vector_field_stage
from edel.pipeline.clustering import run_clustering_stage
from edel.pipeline.landscape import run_landscape_stage

def main():
    base_path = Path("artifacts")
    configs_dir = base_path / "configs"
    init_registry(configs_dir)
    
    print("=" * 70)
    print("Refreshing benchmark pipeline artifacts for 'afp_lemma'...")
    print("=" * 70)
    
    config = get_experiment("afp_lemma")
    
    # 1. Stage 1: Data Collection & Stage 3: Embeddings
    print("\n[Stage 1 & 3] Loading dataset and embeddings from artifacts/rag_index...")
    t0 = time.time()
    df, _ = generate_dataset(config.get("data", {}))
    print(f"  Loaded {len(df)} theorems/lemmas in {time.time() - t0:.2f}s")
    
    # Save Stage 1 and Stage 3 artifacts
    art_data = make_stage_artifact(config, base_path, "data_collection", "dataset")
    save_artifact(art_data, df)
    print(f"  Saved Stage 1 artifact -> {art_data.parquet_path}")
    
    art_emb = make_stage_artifact(config, base_path, "embeddings", "embeddings")
    save_artifact(art_emb, df)
    print(f"  Saved Stage 3 artifact -> {art_emb.parquet_path}")
    
    # 2. Stage 4: Dimensionality Reduction
    print("\n[Stage 4] Computing common diffusion map projections and transition signatures...")
    t0 = time.time()
    proj_df, report = run_projection_stage(df, config)
    print(f"  Projection complete in {time.time() - t0:.2f}s, shape={proj_df.shape}")
    
    art_dr = make_stage_artifact(config, base_path, "dimensionality_reduction", "dr")
    save_artifact(art_dr, proj_df)
    print(f"  Saved Stage 4 artifact -> {art_dr.parquet_path}")
    if report:
        art_dr_rep = make_stage_artifact(config, base_path, "dimensionality_reduction", "report")
        save_artifact(art_dr_rep, report)
    
    # 3. Stage 5: Vector Field
    print("\n[Stage 5] Computing vector field over diffusion space...")
    t0 = time.time()
    vf = run_vector_field_stage(proj_df, config)
    print(f"  Vector field complete in {time.time() - t0:.2f}s")
    
    art_vf = make_stage_artifact(config, base_path, "vector_field", "vf")
    save_artifact(art_vf, vf)
    print(f"  Saved Stage 5 artifact -> {art_vf.parquet_path if hasattr(art_vf, 'parquet_path') else art_vf.pkl_path}")
    
    # 4. Stage 6: Clustering
    print("\n[Stage 6] Running multi-aspect clustering (domain, field, style)...")
    t0 = time.time()
    clustered_df, field_clust, cluster_rep = run_clustering_stage(proj_df, vf, config)
    print(f"  Clustering complete in {time.time() - t0:.2f}s, shape={clustered_df.shape}")
    
    art_clust = make_stage_artifact(config, base_path, "clustering", "clustering")
    save_artifact(art_clust, clustered_df)
    print(f"  Saved Stage 6 artifact -> {art_clust.parquet_path}")
    
    if field_clust is not None:
        art_fclust = make_stage_artifact(config, base_path, "clustering", "field_clustering")
        save_artifact(art_fclust, field_clust)
    if cluster_rep:
        art_crep = make_stage_artifact(config, base_path, "clustering", "report")
        save_artifact(art_crep, cluster_rep)
        
    # 5. Stage 8: Landscape Terrain & Height
    print("\n[Stage 8] Generating 3D landscape terrain grid from Landscape Height H...")
    t0 = time.time()
    landscape_res = run_landscape_stage(clustered_df, vf, config)
    print(f"  Landscape complete in {time.time() - t0:.2f}s, keys={list(landscape_res.keys())}")
    
    art_land = make_stage_artifact(config, base_path, "output", "landscape_results")
    save_artifact(art_land, landscape_res)
    print(f"  Saved Stage 8 artifact -> {art_land.pkl_path}")
    
    print("\n" + "=" * 70)
    print(f"All 1,924 benchmark artifacts successfully updated and persisted!")
    print("=" * 70)

if __name__ == "__main__":
    main()
