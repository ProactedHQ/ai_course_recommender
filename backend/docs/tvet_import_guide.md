# TVET Data Import Guide

This document outlines the high-performance pipeline used to extract, clean, and import TVET (Technical and Vocational Education and Training) data into the system.

## Pipeline Architecture

1.  **Extraction**: `scripts/tvet_pdf_to_json.py`
    -   Uses `pdfplumber` to parse official KUCCPS PDFs.
    -   Handles three distinct document structures: Artisan, Craft, and Certificate.
    -   Implements strict heading detection to prevent text "stickiness" in trade/cluster names.
2.  **Cleaning**: `scripts/cleanup_tvet_data.py`
    -   Surgically removes existing TVET data to allow for clean re-imports.
    -   Uses a dry-run mode for safety.
3.  **Bulk Loading**: `scripts/tvet_json_to_db.py`
    -   **Optimized Phased Load**: Reduces import time from hours to seconds (< 45s for 6.5k records).
    -   **Deduplication**: Handles duplicate `kuccps_code` and `(programme, institution)` pairs in source data.
    -   **Idempotency**: Explicitly cleans up old offerings before bulk creating new ones.
    -   **Windows Compatibility**: Uses ASCII-only logging to avoid `UnicodeEncodeError`.

## How to Re-run

If new TVET data is released:

1.  Place the new PDFs in the `backend/` directory.
2.  Run the extractor:
    ```bash
    venv/Scripts/python.exe scripts/tvet_pdf_to_json.py
    ```
3.  Run the bulk loader:
    ```bash
    venv/Scripts/python.exe scripts/tvet_json_to_db.py
    ```

## Data Models Involved

-   **`Programme`**: Unique by `kuccps_code`.
-   **`ProgrammeLevel`**: ARTISAN, CRAFT, CERTIFICATE, DIPLOMA, DEGREE.
-   **`ClusterGroup`**: Represents the "Trade" or category.
-   **`ProgrammeOffering`**: Links programs to Institutions.
-   **`ProgrammeRequirement`**: Stores the raw requirements string.

## Contributors Note

When modifying the loader, always use `bulk_create` and `bulk_update` with a `batch_size` (e.g., 500) to maintain high performance. Avoid calling `.save()` inside loops.
