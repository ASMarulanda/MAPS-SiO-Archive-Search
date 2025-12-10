## MAPS SiO Archive Search Pipeline

This folder contains a reproducible Python pipeline designed to search the ALMA public archive for SiO(v=0) rotational transitions toward the MAPS disk sample:

* IM Lup
* AS 209
* GM Aur
* HD 163296
* MWC 480

The primary goal is to identify all archival ALMA observations whose spectral windows accidentally or intentionally include any $\mathrm{SiO}(\nu=0)$ line from $J=1\text{--}0$ to $J=20\text{--}19$. The pipeline generates a clean list of datasets (MOUS IDs) ready for downloading and subsequent imaging and analysis.

## 🔍 What this pipeline does

Queries the ALMA archive (public access only) using the TAP/ObsCore interface via the ALminer Python package.

For each MAPS source, performs a cone search with a radius of 1 arcminute.

For every returned spectral window (SPW), checks whether its frequency range $[\nu_{\mathrm{min}}, \nu_{\mathrm{max}}]$ contains any $\mathrm{SiO}(\nu=0)$ rest frequency from $J=1\text{--}0$ through $J=20\text{--}19$.

Collects all positive matches and generates two key output tables:

Per-SPW table: one row per spectral window containing $\mathrm{SiO}$ coverage.

Per-MOUS table: one row per dataset (MOUS ID), grouping all $\mathrm{SiO}$ transitions found within that scheduling block.

Optionally downloads all public MOUS datasets using astroquery.alma.

This pipeline implements the MAPS pre-filter and download step described in the thesis.

## 📁 Files in this folder

maps_sio_archive_search.py: The main script that performs archive querying, spectral-window filtering, table generation, and optional downloading.

README.md: (This file)

example_output/ (optional): Contains example exported tables for reference:

sio_spw_matches.csv

sio_mous_summary.csv

## 📦 Installation

It is highly recommended to use a virtual environment:

python3 -m venv venv
source venv/bin/activate


Install required packages:

pip install alminer astroquery pandas


Note: No ALMA login is needed, as the script uses public archive access only.

##  ▶️ How to run

From inside this folder (maps_sio_archive_search/):

python maps_sio_archive_search.py


The script will automatically:

Query ALMA for all public observations of IM Lup, AS 209, GM Aur, HD 163296, and MWC 480.

Identify all spectral windows that include any $\mathrm{SiO}(\nu=0)$ transition.

Export four files:

sio_spw_matches.csv

sio_spw_matches.tex

sio_mous_summary.csv

sio_mous_summary.tex

## 📊 Output Tables

1. Per-SPW Table (sio_spw_matches.*)

Each row corresponds to one spectral window that covers an $\mathrm{SiO}$ transition. This table is useful for tracking which specific projects and SPWs contain the desired spectral coverage.

Key Columns Include:

Source
Project
ALMA_Band
min_freq_GHz, max_freq_GHz (The spectral window boundaries)
SiO_transition, SiO_freq_GHz (The specific transition found)
ang_res_arcsec
MOUS_ID

2. Per-MOUS Table (sio_mous_summary.*)
Each row corresponds to a single ALMA dataset (MOUS ID). This table summarizes all $\mathrm{SiO}$ coverage within that dataset and is the primary table used for determining which datasets to download and pass to the next analysis stage.

Key Columns Include:
MOUS_ID
Source
Project
ALMA_Band
SiO_transitions (List of all transitions found in this MOUS)
SiO_freqs_GHz
min_freq_GHz, max_freq_GHz (The total frequency range covered by the MOUS)
ang_res_arcsec (Angular resolution of the observation)

## 💾 Optional: Automatic Download of MOUS Datasets

Inside maps_sio_archive_search.py, its possible to change the configuration variable:
DO_DOWNLOAD = True
Setting this to True triggers automated retrieval for each public MOUS listed in sio_mous_summary.csv using the Alma().retrieve_data_from_uid(mous_id) function.

## ⚠️ Warning: Some datasets are very large (GB-scale). Download is OFF by default to avoid unintended transfers.
