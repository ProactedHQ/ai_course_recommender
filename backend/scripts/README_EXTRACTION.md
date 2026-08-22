# Degree Cluster Extraction V2 - User Guide

## Overview
This script extracts cluster, subcluster, and subject requirement data from `DEGREE_CLUSTER_DOCUMENT_2025_03.pdf` and outputs to JSON for manual verification.

## Installation
Ensure you have `pdfplumber` installed:
```bash
pip install pdfplumber
```

## Usage

### Basic Usage (Extract All Pages)
```bash
python scripts/extract_degree_clusters_v2.py
```

### Extract Specific Pages
```bash
# Extract only pages 1-3
python scripts/extract_degree_clusters_v2.py --pages 1-3

# Extract page 5
python scripts/extract_degree_clusters_v2.py --pages 5-5
```

### Custom Output File
```bash
python scripts/extract_degree_clusters_v2.py --output my_clusters.json
```

## Output Format

The script generates JSON with this structure:

```json
{
  "clusters": [
    {
      "code": "7",
      "name": "Computing Sciences",
      "subject_1": null,
      "subject_2": null,
      "subject_3": null,
      "subject_4": null,
      "subclusters": [
        {
          "code": "7A",
          "subject_1": "ENG - C+",
          "subject_2": "MAT A - B",
          "subject_3": "PHY - C+",
          "subject_4": "GEO - C",
          "programmes": [
            "Bachelor of Science in Software Engineering",
            "Bachelor of Science in Computer Science"
          ]
        },
        {
          "code": "7B",
          "subject_1": "ENG - C+",
          "subject_2": "MAT B - C+",
          "subject_3": "CHE - C+",
          "subject_4": "BIO - C",
          "programmes": [
            "Bachelor of Science in Information Technology"
          ]
        }
      ]
    }
  ]
}
```

## Manual Verification Steps

After extraction:

1. **Open the JSON file**: `extraction_output/degree_clusters_v2.json`

2. **Verify each cluster**:
   - Check cluster code matches PDF (1-20)
   - Check cluster name is correct
   - Verify subject requirements are properly formatted

3. **Verify each subcluster**:
   - Check subcluster codes (e.g., "7A", "7B")
   - Verify subject requirements match the green row in PDF
   - Ensure programme names are complete and accurate

4. **Common Issues to Fix**:
   - Missing or incomplete programme names
   - Incorrect subject-grade combinations
   - Wrong subcluster codes
   - Programmes assigned to wrong subcluster

5. **Edit the JSON** directly to fix any errors

6. **Save corrected JSON** for database seeding

## What the Script Does

1. **Finds Clusters**: Looks for cluster codes (1-20) in first column
2. **Finds Subclusters**: Looks for alphanumeric codes like "7A", "2B"
3. **Extracts Subject Categories**: Identifies yellow header rows
4. **Extracts Grades**: Identifies green requirement rows
5. **Combines**: Merges category + grade (e.g., "MAT ALT A" + "C+" = "MAT ALT A - C+")
6. **Extracts Programmes**: Finds all "Bachelor of..." entries under each subcluster

## Troubleshooting

### No tables found
- PDF might be image-based (requires OCR)
- Try different page range

### Missing programmes
- Programme names may be in unexpected format
- Manually add to JSON after extraction

### Incorrect subject requirements
- PDF table structure might vary
- Manually correct in JSON

### Wrong subcluster assignment
- Table parsing may misidentify boundaries
- Manually reassign programmes in JSON

## Next Steps

After you've verified and corrected the JSON:

1. Run the updated `seed_data` command (to be created)
2. Verify data in Django Admin
3. Check foreign key relationships

## Tips

- **Start small**: Extract 1-2 pages first to test
- **Compare side-by-side**: Open PDF and JSON together
- **Focus on accuracy**: It's okay to manually fix JSON
- **Document issues**: Note any patterns for script improvement
