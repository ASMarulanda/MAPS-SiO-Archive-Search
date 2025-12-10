#!/usr/bin/env python3
"""
MAPS SiO archive search (public ALMA data only)

This script:
  1) Queries all public ALMA observations for MAPS disk sources.
  2) Identifies any spectral window whose frequency range contains
     at least one SiO(v=0) transition from J=1–0 to J=20–19.
  3) Produces:
        - sio_spw_matches.csv / .tex      (per SPW)
        - sio_mous_summary.csv / .tex     (per MOUS)
  4) Optional: downloads all public SiO-covering MOUS IDs
     using astroquery.alma.
"""

from __future__ import annotations
from typing import List, Dict
import pandas as pd
import alminer
from astroquery.alma import Alma


# --------------------------------------------------------------------
# 1. User configuration, add list of sources in the MAP Project 
# --------------------------------------------------------------------

MAPS_SOURCES = ["IM Lup", "AS 209", "GM Aur", "HD 163296", "MWC 480"]

# SiO(v=0) transitions in GHz used for the search 
SIO_V0_TRANSITIONS_GHZ: Dict[str, float] = {
    "J=1-0":   43.423864,
    "J=2-1":   86.846960,
    "J=3-2":  130.268610,
    "J=4-3":  173.688310,
    "J=5-4":  217.104980,
    "J=6-5":  260.518200,
    "J=7-6":  303.927030,
    "J=8-7":  347.331000,
    "J=9-8":  390.728730,
    "J=10-9": 434.120450,
    "J=11-10":477.506120,
    "J=12-11":520.885480,
    "J=13-12":564.258560,
    "J=14-13":607.625260,
    "J=15-14":650.985560,
    "J=16-15":694.339440,
    "J=17-16":737.686780,
    "J=18-17":781.027470,
    "J=19-18":824.361490,
    "J=20-19":867.688720,
}

TAP_SERVICE = "ESO"          # ESO mirror is most reliable than ALMA 
SEARCH_RADIUS_ARCMIN = 1.0   # Cone-search radius
DO_DOWNLOAD = False          # Set to True to download MOUS datasets


# --------------------------------------------------------------------
# 2. Query ALMA Archive (public only) for ALL MAPS sources
# --------------------------------------------------------------------

def query_maps_sources(sources: List[str]) -> pd.DataFrame:
    """
    Loop over MAPS sources and query each one with ALminer.target().
    Explicitly tag each row with the MAPS source name in a 'Source' column.
    """
    all_obs = []

    for src in sources:
        print(f"\n=== Querying ALMA archive for: {src} ===")
        try:
            df = alminer.target(
                [src],
                search_radius=SEARCH_RADIUS_ARCMIN,
                tap_service=TAP_SERVICE,
                point=False,          # cone search
                public=True,          # public data only
                published=None,       # both published and unpublished
                print_query=False,
                print_targets=True,
            )
        except Exception as exc:
            print(f"  Query failed for {src}: {exc}")
            continue

        if df is None or len(df) == 0:
            print(f"  No ObsCore rows returned for {src}.")
            continue

        df = df.copy()
        # Tag everything returned in this query with the MAPS source name
        df["Source"] = src
        all_obs.append(df)

    if not all_obs:
        raise RuntimeError("No observations returned for any MAPS source.")

    combined = pd.concat(all_obs, ignore_index=True)

    print("\nRows per MAPS source in ObsCore results:")
    print(combined["Source"].value_counts())

    print(f"\nTotal ObsCore rows retrieved: {len(combined)}")
    return combined


# --------------------------------------------------------------------
# 3. Standardize and clean ObsCore fields
# --------------------------------------------------------------------

def harmonize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Angular resolution
    if "ang_res_arcsec" not in df.columns:
        if "best_ang_res" in df.columns:
            df["ang_res_arcsec"] = df["best_ang_res"]
        else:
            df["ang_res_arcsec"] = float("nan")

    # Band column
    if "band_list" not in df.columns and "band" in df.columns:
        df["band_list"] = df["band"]

    # Frequency columns
    for col in ("min_freq_GHz", "max_freq_GHz"):
        if col not in df.columns:
            raise KeyError(f"Missing required ObsCore column: {col}")

    # MOUS ID
    if "member_ous_uid" in df.columns:
        df["MOUS_ID"] = df["member_ous_uid"]
    elif "member_ous_id" in df.columns:
        df["MOUS_ID"] = df["member_ous_id"]
    else:
        raise KeyError(
            "ObsCore table missing MOUS identifier (member_ous_uid / member_ous_id)."
        )

    return df


# --------------------------------------------------------------------
# 4. Frequency filtering for SiO(v=0)
# --------------------------------------------------------------------

def find_sio_spw_matches(obs_df: pd.DataFrame) -> pd.DataFrame:
    matches = []

    for trans, nu in SIO_V0_TRANSITIONS_GHZ.items():
        mask = (obs_df["min_freq_GHz"] < nu) & (obs_df["max_freq_GHz"] > nu)
        sel = obs_df[mask].copy()
        if len(sel):
            sel["SiO_transition"] = trans
            sel["SiO_freq_GHz"] = nu
            matches.append(sel)

    if not matches:
        print("No SPWs cover any SiO(v=0) lines.")
        return pd.DataFrame()

    all_matches = pd.concat(matches, ignore_index=True)
    print(f"\nTotal SiO-covering SPW rows: {len(all_matches)}")

    # Quick check: how many SiO SPWs per MAPS source?
    print("\nSiO-covering SPWs per MAPS source:")
    print(all_matches["Source"].value_counts())

    return all_matches


# --------------------------------------------------------------------
# 5. Build per-SPW and per-MOUS tables
# --------------------------------------------------------------------

def build_per_spw_table(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [
        "Source", "project_code", "band_list",
        "min_freq_GHz", "max_freq_GHz",
        "SiO_transition", "SiO_freq_GHz",
        "ang_res_arcsec", "MOUS_ID",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]

    spw = df[keep_cols].rename(columns={
        "project_code": "Project",
        "band_list": "ALMA_Band",
    })

    return spw.sort_values(
        ["Source", "Project", "ALMA_Band", "SiO_freq_GHz"]
    )


def build_per_mous_table(df: pd.DataFrame) -> pd.DataFrame:
    def join_unique(series):
        return ", ".join(sorted(series.astype(str).unique()))

    grouped = (
        df.groupby("MOUS_ID")
          .agg({
              "Source": join_unique,
              "project_code": join_unique,
              "band_list": join_unique,
              "min_freq_GHz": "min",
              "max_freq_GHz": "max",
              "SiO_transition": join_unique,
              "SiO_freq_GHz": join_unique,
              "ang_res_arcsec": "min",
          })
          .reset_index()
    )

    grouped = grouped.rename(columns={
        "project_code": "Project",
        "band_list": "ALMA_Band",
        "SiO_transition": "SiO_transitions",
        "SiO_freq_GHz": "SiO_freqs_GHz",
    })

    print(f"\nTotal unique MOUS IDs with SiO coverage: {len(grouped)}")
    return grouped.sort_values(["Source", "Project"])


# --------------------------------------------------------------------
# 6. Save all output tables
# --------------------------------------------------------------------

def save_tables(spw: pd.DataFrame, mous: pd.DataFrame) -> None:
    spw.to_csv("sio_spw_matches.csv", index=False)
    mous.to_csv("sio_mous_summary.csv", index=False)

    with open("sio_spw_matches.tex", "w") as f:
        f.write(
            spw.to_latex(
                index=False,
                float_format="%.6f",
                columns=[
                    "Source", "Project", "ALMA_Band",
                    "min_freq_GHz", "max_freq_GHz",
                    "SiO_transition", "SiO_freq_GHz",
                    "ang_res_arcsec"
                ]
            )
        )

    with open("sio_mous_summary.tex", "w") as f:
        f.write(
            mous.to_latex(
                index=False,
                float_format="%.6f",
                columns=[
                    "MOUS_ID", "Source", "Project", "ALMA_Band",
                    "SiO_transitions", "SiO_freqs_GHz",
                    "min_freq_GHz", "max_freq_GHz",
                    "ang_res_arcsec"
                ]
            )
        )

    print("\nSaved: sio_spw_matches.*, sio_mous_summary.*")


# --------------------------------------------------------------------
# 7. Optional: Download SiO-covering MOUS IDs
# --------------------------------------------------------------------

def download_mous_products(mous_table: pd.DataFrame) -> None:
    alma = Alma()     # public access only
    uids = mous_table["MOUS_ID"].unique()

    print(f"\nDownloading {len(uids)} public MOUS datasets...\n")

    for uid in uids:
        print(f"Retrieving {uid} ...")
        try:
            alma.retrieve_data_from_uid(uid, cache=True)
        except Exception as exc:
            print(f"  Failed to download {uid}: {exc}")


# --------------------------------------------------------------------
# 8. Main execution
# --------------------------------------------------------------------

def main():
    print("\n==== MAPS SiO Archive Search ====\n")

    obs = query_maps_sources(MAPS_SOURCES)
    obs = harmonize_columns(obs)

    sio_spw = find_sio_spw_matches(obs)
    if sio_spw.empty:
        print("No SiO SPWs found. Exiting.")
        return

    spw_table = build_per_spw_table(sio_spw)
    mous_table = build_per_mous_table(sio_spw)

    save_tables(spw_table, mous_table)

    if DO_DOWNLOAD:
        download_mous_products(mous_table)
    else:
        print("\nDownload stage disabled (DO_DOWNLOAD=False)")


if __name__ == "__main__":
    main()
