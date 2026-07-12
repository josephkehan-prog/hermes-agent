---
name: bioinformatics
description: Gateway to 400+ bioinformatics skills from bioSkills and ClawBio. Covers genomics, transcriptomics, single-cell, variant calling, pharmacogenomics, metagenomics, structural biology, and more. Fetches domain-specific reference material on demand.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [bioinformatics, genomics, sequencing, biology, research, science]
    category: research
---

# Bioinformatics Skills Gateway

Use when asked about bioinformatics, genomics, sequencing, variant calling, gene expression, single-cell analysis, protein structure, pharmacogenomics, metagenomics, phylogenetics, or any computational biology task.

This skill is a gateway to two open-source bioinformatics skill libraries. Instead of bundling hundreds of domain-specific skills, it indexes them and fetches what you need on demand.

## Sources

◆ **bioSkills** — 385 reference skills (code patterns, parameter guides, decision trees)
  Repo: https://github.com/GPTomics/bioSkills
  Format: SKILL.md per topic with code examples. Python/R/CLI.

◆ **ClawBio** — 33 runnable pipeline skills (executable scripts, reproducibility bundles)
  Repo: https://github.com/ClawBio/ClawBio
  Format: Python scripts with demos. Each analysis exports report.md + commands.sh + environment.yml.

## How to fetch and use a skill

1. Identify the domain and skill name from the index below.
2. Clone the relevant repo (shallow clone to save time):
   ```bash
   # bioSkills (reference material)
   git clone --depth 1 https://github.com/GPTomics/bioSkills.git /tmp/bioSkills

   # ClawBio (runnable pipelines)
   git clone --depth 1 https://github.com/ClawBio/ClawBio.git /tmp/ClawBio
   ```
3. Read the specific skill:
   ```bash
   # bioSkills — each skill is at: <category>/<skill-name>/SKILL.md
   cat /tmp/bioSkills/variant-calling/gatk-variant-calling/SKILL.md

   # ClawBio — each skill is at: skills/<skill-name>/
   cat /tmp/ClawBio/skills/pharmgx-reporter/README.md
   ```
4. Follow the fetched skill as reference material. These are NOT Hermes-format skills — treat them as expert domain guides. They contain correct parameters, proper tool flags, and validated pipelines.

## Domains Covered

Pick the domain that matches the task, then read `references/index.md` for
the exact bioSkills path / ClawBio skill name to fetch and read (per "How to
fetch and use a skill" above).

| Domain | Covers |
|---|---|
| Sequence Fundamentals | Read/write/format-convert sequences, QC, manipulation |
| Read QC & Alignment | fastp, BWA/STAR/HISAT2/Bowtie2, SAM/BAM handling |
| Variant Calling & Annotation | GATK, DeepVariant, bcftools, VCF manipulation, VEP/ClinVar/gnomAD |
| Differential Expression (bulk RNA-seq) | DESeq2, edgeR, Salmon/kallisto, featureCounts |
| Single-Cell RNA-seq | Scanpy/Seurat pipeline, clustering, batch integration, trajectory |
| Spatial Transcriptomics | Spatial data I/O, domains, deconvolution, multiomics |
| Epigenomics | ChIP-seq, ATAC-seq, methylation (Bismark), Hi-C |
| Pharmacogenomics & Clinical | ClinVar/gnomAD/dbSNP, PGx reports, GWAS/PRS lookup |
| Population Genetics & GWAS | PLINK, causal genomics, phasing/imputation, ancestry PCA |
| Metagenomics & Microbiome | Kraken/MetaPhlAn, amplicon processing, QIIME2 |
| Genome Assembly & Annotation | HiFi/long/short-read assembly, gene prediction, ONT basecalling |
| Structural Biology & Chemoinformatics | AlphaFold/Boltz/Chai, molecular descriptors, virtual screening |
| Proteomics | Peptide ID, protein inference, DIA, PTM analysis |
| Pathway Analysis & Gene Networks | GO/GSEA/KEGG/Reactome, SCENIC, co-expression networks |
| Immunoinformatics | MHC binding, epitope/neoantigen prediction, TCR/BCR repertoire |
| CRISPR & Genome Engineering | MAGeCK screens, gRNA design, base/prime editing |
| Workflow Management | Snakemake, Nextflow, CWL, WDL, reproducibility bundles |
| Specialized Domains | Splicing, ecological/epidemiological genomics, liquid biopsy, epitranscriptomics, metabolomics, flow cytometry, systems biology, RNA structure |
| Data Visualization & Reporting | ggplot2, heatmaps, circos, R Markdown/Quarto reports, lit search |
| Database Access | Entrez, BLAST, SRA/GEO, UniProt, UK Biobank, clinical trials |
| Experimental Design | Power analysis, sample size, batch design |
| Machine Learning for Omics | Omics classifiers, biomarker discovery, survival analysis |

Full skill-name listing per domain: `references/index.md`.

## Environment Setup

These skills assume a bioinformatics workstation. Common dependencies:

```bash
# Python
pip install biopython pysam cyvcf2 pybedtools pyBigWig scikit-allel anndata scanpy mygene

# R/Bioconductor
Rscript -e 'BiocManager::install(c("DESeq2","edgeR","Seurat","clusterProfiler","methylKit"))'

# CLI tools (Ubuntu/Debian)
sudo apt install samtools bcftools ncbi-blast+ minimap2 bedtools

# CLI tools (macOS)
brew install samtools bcftools blast minimap2 bedtools

# Or via Conda (recommended for reproducibility)
conda install -c bioconda samtools bcftools blast minimap2 bedtools fastp kraken2
```

## Pitfalls

- The fetched skills are NOT in Hermes SKILL.md format. They use their own structure (bioSkills: code pattern cookbooks; ClawBio: README + Python scripts). Read them as expert reference material.
- bioSkills are reference guides — they show correct parameters and code patterns but aren't executable pipelines.
- ClawBio skills are executable — many have `--demo` flags and can be run directly.
- Both repos assume bioinformatics tools are installed. Check prerequisites before running pipelines.
- For ClawBio, run `pip install -r requirements.txt` in the cloned repo first.
- Genomic data files can be very large. Be mindful of disk space when downloading reference genomes, SRA datasets, or building indices.
