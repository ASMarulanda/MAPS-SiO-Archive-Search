# MAPS SiO(v=0) Archive Search Pipeline

This folder contains a complete, reproducible Python pipeline for identifying **all ALMA archival observations** toward the **MAPS disk sample** that include **any SiO(v=0) rotational transition** from  
**J = 1→0** up to **J = 20→19**.

The MAPS targets processed by this pipeline are:

- IM Lup  
- AS 209  
- GM Aur  
- HD 163296  
- MWC 480  

The goal is to produce a clean list of ALMA datasets (MOUS IDs) whose spectral windows cover at least one SiO(v=0) transition, enabling automated download, calibration, and imaging in subsequent stages of the thesis pipeline.

---

## Contents

```
maps_sio_archive_search.py      # Main pipeline script
sio_spw_matches.csv             # Per-SPW SiO match table (auto-generated)
sio_spw_matches.tex             # Per-SPW table in LaTeX format
sio_mous_summary.csv            # Per-MOUS SiO summary table (auto-generated)
sio_mous_summary.tex            # Per-MOUS table in LaTeX format
README.md                       # This file
```

---

## Pipeline Overview

### 1. Query ALMA Archive (ObsCore/TAP)

The script uses **ALminer** to perform a 1 arcmin cone search around each MAPS source.  
All public archival observations matching the coordinate search are returned.

### 2. Identify SiO-Covering Spectral Windows

For each returned spectral window (SPW), the script evaluates whether the frequency range  
\[
[
u_{\min}, 
u_{\max}]
\]
contains any of the **20 SiO(v=0)** rotational transitions from J=1–0 to J=20–19.

### 3. Build Output Tables

The script generates two structured products:

#### Per-SPW Table (`sio_spw_matches.*`)
Each row corresponds to a single SPW containing at least one SiO transition.  
Columns include:

- Source  
- Project  
- ALMA Band  
- min\_freq\_GHz, max\_freq\_GHz  
- SiO\_transition, SiO\_freq\_GHz  
- ang\_res\_arcsec  
- MOUS\_ID  

#### Per-MOUS Table (`sio_mous_summary.*`)
Each row corresponds to a unique MOUS ID and aggregates all SPWs and SiO transitions found in that dataset.

Columns include:

- MOUS\_ID  
- Source  
- Project  
- ALMA Band  
- SiO\_transitions  
- SiO\_freqs\_GHz  
- min\_freq\_GHz, max\_freq\_GHz  
- ang\_res\_arcsec  

This table defines the **final list of SiO-sensitive datasets** used for downstream analysis.

---

## Installation

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install alminer astroquery pandas numpy
```

No ALMA login is required; the script only accesses public archive data.

---

## Running the Pipeline

From inside this folder (`maps_sio_archive_search/`):

```bash
python3 maps_sio_archive_search.py
```

The script will:

1. Query ALMA for all MAPS sources  
2. Identify any SPWs covering SiO(v=0) transitions  
3. Generate:
   - `sio_spw_matches.csv`  
   - `sio_spw_matches.tex`  
   - `sio_mous_summary.csv`  
   - `sio_mous_summary.tex`  

---

## Optional: Automatic Dataset Download

Inside `maps_sio_archive_search.py`, set:

```python
DO_DOWNLOAD = True
```

This will trigger:

```python
Alma().retrieve_data_from_uid(mous_id)
```

for every MOUS listed in `sio_mous_summary.csv`.

**Warning:**  
Some ALMA datasets exceed multiple gigabytes.  
Downloading is disabled by default to avoid accidental large transfers.

---

## License

MIT License.

--------------------------------------------------------------------------------
