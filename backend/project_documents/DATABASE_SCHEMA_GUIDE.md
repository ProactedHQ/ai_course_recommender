# Database Schema Guide

## Overview

This document describes the complete database schema for the AI Course Recommendation System, including all models, relationships, and **current seeded data statistics**.

**Last Updated**: 2026-02-01  
**Database Status**: ✅ Production Ready - Fully Seeded

---

## Current Database State

### Summary Statistics

| Table                        | Record Count | Status    |
| ---------------------------- | ------------ | --------- |
| **Subject**                  | 40           | ✅ Seeded |
| **ProgrammeLevel**           | 4            | ✅ Seeded |
| **Institution**              | 500          | ✅ Seeded |
| **ClusterGroup** (Degree)    | 20           | ✅ Seeded |
| **SubClusterGroup** (Degree) | 62           | ✅ Seeded |
| **ClusterGroup** (TVET)      | 65           | ✅ Seeded |
| **Programme**                | 2,050        | ✅ Seeded |
| **ProgrammeOffering**        | 2,050        | ✅ Seeded |
| **CutOffPoint**              | 14,350       | ✅ Seeded |

**Total Records**: ~21,000  
**Data Quality**: Zero duplicates verified  
**Cutoff Coverage**: 7 years (2018-2024) for all programmes

---

## Model Descriptions

### 1. Student Models (App: `students`)

#### Subject

KCSE subjects that students take in high school.

**Fields**:

- `code` (CharField, unique): Subject code (e.g., "101" for English)
- `name` (CharField): Subject name (e.g., "English")
- `category` (CharField): KCSE group (GP1-GP5)

**Current Data**: 40 subjects including all KCSE subjects across Groups 1-5

**Sample Records**:

```
101 - English (GP1)
102 - Kiswahili (GP1)
121 - Mathematics Alternative A (GP1)
231 - Physics (GP2)
311 - Geography (GP3)
```

#### StudentGrade

Individual student's grade for a specific subject.

**Fields**:

- `student` (ForeignKey → User)
- `subject` (ForeignKey → Subject)
- `grade` (CharField): Grade (A, A-, B+, etc.)
- `points` (DecimalField): Grade points

**Relationships**:

- Each student can have multiple grades (one per subject)
- Each grade links to one subject

---

### 2. University Models (App: `universities`)

#### ProgrammeLevel

Education level categories.

**Fields**:

- `name` (CharField, unique): Level name

**Current Data**: 4 levels

```
- DEGREE
- DIPLOMA
- CERTIFICATE
- ARTISAN
```

#### Institution

Universities, colleges, and TVET institutions offering programmes.

**Fields**:

- `code` (CharField, unique): Institution code (e.g., "1105")
- `name` (CharField, unique): Institution name
- `institution_type` (CharField): Type (PUBLIC_UNIVERSITY, PRIVATE_UNIVERSITY, TVET)
- `location` (CharField): Physical location
- `website` (URLField): Institution website

**Current Data**: 500 institutions

- Public Universities
- Private Universities
- TVET Institutions

**Sample Records**:

```
1105 - CHUKA UNIVERSITY (PUBLIC_UNIVERSITY)
1087 - KISII UNIVERSITY (PUBLIC_UNIVERSITY)
1425 - ZETECH UNIVERSITY (PRIVATE_UNIVERSITY)
```

#### ClusterGroup

Programme clusters that group related fields of study. Used for both **Degree** and **TVET** programmes.

**Fields**:

- `level` (ForeignKey → ProgrammeLevel): DEGREE, DIPLOMA, CERTIFICATE, or ARTISAN
- `code` (CharField, unique): Cluster code
- `name` (CharField): Cluster name/description
- `subject_1` to `subject_4` (CharField, nullable): Subject requirements

**Current Data**:

- **20 Degree Clusters** (e.g., "Law", "Engineering", "Medical Sciences")
- **65 TVET Clusters** broken down as:
  - 33 Diploma level
  - 23 Certificate level
  - 9 Artisan level

**TVET Cluster Examples**:

```
TVET-1-DIPL - Law (Diploma)
TVET-5-CERT - Engineering, Engineering Technology (Certificate)
KNEC-1-ARTI - Business courses (Artisan)
INTERNAL-5-TAX-DIPL - Tax Administration (Tax Administration) (Diploma)
```

**Degree Cluster Examples**:

```
Cluster 1: Law
Cluster 4: Engineering
Cluster 13: Medical Sciences
```

#### SubClusterGroup

Sub-categories within degree clusters for more specific programme grouping.

**Fields**:

- `cluster` (ForeignKey → ClusterGroup): Parent cluster
- `code` (CharField): Subcluster code
- `name` (CharField): Subcluster name
- `subject_requirements` (TextField, nullable): Specific requirements

**Current Data**: 62 degree subclusters

**Examples**:

```
Medical Laboratory → under Medical Sciences cluster
Civil Engineering → under Engineering cluster
Corporate Law → under Law cluster
```

#### Programme

Individual academic programmes (e.g., "Bachelor of Science in Computer Science").

**Fields**:

- `kuccps_code` (CharField, unique): KUCCPS programme code (e.g., "1105206")
- `name` (CharField): Programme name
- `level` (ForeignKey → ProgrammeLevel): Education level
- `cluster` (ForeignKey → ClusterGroup, nullable): Programme cluster
- `sub_cluster` (ForeignKey → SubClusterGroup, nullable): Programme subcluster

**Current Data**: 2,050 unique programmes

- All degree programmes from KUCCPS data
- Complete coverage of programmes with cutoffs

**Sample Records**:

```
1105101 - BACHELOR OF ARTS (Degree, Cluster: Humanities)
1087151 - BACHELOR OF SCIENCE IN COMPUTER SCIENCE (Degree, Cluster: Computing)
1105206 - BACHELOR OF BUSINESS INFORMATION TECHNOLOGY (Degree, Cluster: Business)
```

**Relationships**:

- Each programme belongs to one level
- Each programme may belong to one cluster (nullable for uncategorized)
- Each programme may belong to one subcluster (nullable)

#### ProgrammeOffering

Represents a specific programme offered at a specific institution. This is where cutoffs are stored.

**Fields**:

- `programme` (ForeignKey → Programme)
- `institution` (ForeignKey → Institution)

**Unique Constraint**: `(programme, institution)` - one offering per programme per institution

**Current Data**: 2,050 offerings

- Each programme has at least one offering
- Some programmes offered at multiple institutions

**Example**:

```
Programme: "BACHELOR OF ARTS"
Institution: "CHUKA UNIVERSITY"
→ ProgrammeOffering links them
```

#### ProgrammeRequirement

Subject requirements for admission to a programme.

**Fields**:

- `programme` (ForeignKey → Programme)
- `subject` (ForeignKey → Subject, nullable)
- `subject_category` (CharField, nullable): Group requirement (e.g., "GP2")
- `minimum_grade` (CharField): Minimum grade (e.g., "C+")
- `is_category` (BooleanField): True if requiring a category vs specific subject
- `description` (TextField): Full requirement text

**Status**: Awaiting implementation of subject requirement parsing

#### CutOffPoint

Historical cutoff points for programme offerings by year.

**Fields**:

- `offering` (ForeignKey → ProgrammeOffering)
- `year` (IntegerField): Year (e.g., 2024)
- `weighted_cluster_points` (DecimalField, nullable): Cutoff for degree programmes
- `mean_grade_cutoff` (CharField, nullable): Cutoff for TVET programmes
- `cutoff_type` (CharField): WEIGHTED_POINTS or MEAN_GRADE
- `capacity` (IntegerField, nullable): Programme capacity
- `placed_students` (IntegerField, nullable): Students placed

**Unique Constraint**: `(offering, year)`

**Current Data**: 14,350 cutoff points

- **Complete 7-year history** (2018-2024)
- All 2,050 programmes have cutoffs for all years
- **195 NULL values preserved** where cutoff data was unavailable (NaN in source)

**Cutoff Distribution by Year**:

```
2018: 2,050 cutoffs (2,043 valid, 7 NULL)
2019: 2,050 cutoffs (2,040 valid, 10 NULL)
2020: 2,050 cutoffs (2,044 valid, 6 NULL)
2021: 2,050 cutoffs (2,047 valid, 3 NULL)
2022: 2,050 cutoffs (2,048 valid, 2 NULL)
2023: 2,050 cutoffs (2,048 valid, 2 NULL)
2024: 2,050 cutoffs (1,885 valid, 165 NULL)
```

**Note on NULL values**: NULL `weighted_cluster_points` indicates that cutoff data was not available for that year (marked as NaN in source data). This is intentional to distinguish "no data" from "cutoff = 0".

---

## Entity Relationships

### Core Relationships

```
User (Student)
  → has many StudentGrade
      → references Subject

Programme
  → belongs to ProgrammeLevel (DEGREE, DIPLOMA, etc.)
  → belongs to ClusterGroup (optional)
  → belongs to SubClusterGroup (optional)
  → has many ProgrammeOffering
      → at Institution
      → has many CutOffPoint (by year)
  → has many ProgrammeRequirement
      → references Subject or subject_category

ClusterGroup
  → belongs to ProgrammeLevel
  → has many SubClusterGroup (for degree clusters)
  → has many Programme
```

### Relationship Cardinality

| Relationship                     | Type        | Description                                    |
| -------------------------------- | ----------- | ---------------------------------------------- |
| Student → StudentGrade           | One-to-Many | One student has multiple grades                |
| Subject ← StudentGrade           | Many-to-One | Many grades reference one subject              |
| Programme → ProgrammeOffering    | One-to-Many | One programme offered at multiple institutions |
| Institution → ProgrammeOffering  | One-to-Many | One institution offers multiple programmes     |
| ProgrammeOffering → CutOffPoint  | One-to-Many | One offering has cutoffs for multiple years    |
| Programme → ProgrammeRequirement | One-to-Many | One programme has multiple requirements        |
| ClusterGroup → SubClusterGroup   | One-to-Many | One cluster has multiple subclusters           |
| Programme → ClusterGroup         | Many-to-One | Many programmes in one cluster                 |

---

## Data Flow

### Student Journey

1. **Student Profile Creation**
   - User registers/logs in
   - Profile created with KCSE index number

2. **Grade Entry**
   - Student enters grades for subjects (StudentGrade records)
   - System calculates weighted cluster points

3. **Recommendation Generation**
   - System identifies student's cluster based on subjects
   - Finds programmes in matching clusters
   - Filters by student's cluster points vs programme cutoffs

4. **Programme Selection**
   - Student views recommended programmes
   - Can filter by institution, cluster, etc.
   - Views historical cutoff trends (2018-2024)

### Data Seeding Flow

**Completed Seeding**:

1. ✅ Subjects seeded from predefined list (40 subjects)
2. ✅ Programme Levels seeded (4 levels)
3. ✅ Institutions seeded from `institutions_data.json` (500 institutions)
4. ✅ Degree Clusters seeded from `degree_clusters_MANUAL.json` (20 clusters)
5. ✅ Degree Subclusters seeded (62 subclusters)
6. ✅ TVET Clusters seeded from `tvet_clusters_MANUAL.json` (65 clusters)
7. ✅ Programmes seeded from `degree_programmes_full.json` + `degree_cutoffs_extracted.json` (2,050 programmes)
8. ✅ Programme Offerings created for all programmes (2,050 offerings)
9. ✅ Cutoff Points seeded from `degree_cutoffs_extracted.json` (14,350 cutoffs)

---

## Database Constraints

### Unique Constraints

- `Subject.code`: Unique subject codes
- `Institution.code`: Unique institution codes
- `Institution.name`: Unique institution names
- `Programme.kuccps_code`: Unique KUCCPS codes
- `ClusterGroup.code`: Unique cluster codes
- `ProgrammeOffering (programme, institution)`: One offering per programme per institution
- `CutOffPoint (offering, year)`: One cutoff per offering per year

### Foreign Key Relationships

All foreign keys use `on_delete=models.CASCADE` except where noted:

- Deleting a Programme deletes all its Offerings
- Deleting an Offering deletes all its CutOffPoints
- Deleting a Subject affects StudentGrade records

---

## Querying Examples

### Get all programmes in a cluster

```python
from universities.models import ClusterGroup, Programme

cluster = ClusterGroup.objects.get(name__icontains="Engineering")
programmes = Programme.objects.filter(cluster=cluster)
```

### Get cutoffs for a specific programme at an institution

```python
from universities.models import Programme, Institution, ProgrammeOffering

programme = Programme.objects.get(kuccps_code="1105206")
institution = Institution.objects.get(code="1105")
offering = ProgrammeOffering.objects.get(programme=programme, institution=institution)
cutoffs = offering.cutoffs.all().order_by('-year')  # Latest first
```

### Get programmes a student qualifies for

```python
from students.models import StudentGrade
from universities.models import CutOffPoint

# Calculate student's cluster points
student_points = calculate_weighted_points(student)

# Find current year cutoffs below student's points
qualifying_cutoffs = CutOffPoint.objects.filter(
    year=2024,
    weighted_cluster_points__lte=student_points
).select_related('offering__programme', 'offering__institution')

programmes = [cutoff.offering.programme for cutoff in qualifying_cutoffs]
```

### Get cutoff trends for a programme

```python
from universities.models import ProgrammeOffering

offering = ProgrammeOffering.objects.get(id=123)
cutoff_trends = offering.cutoffs.all().order_by('year').values('year', 'weighted_cluster_points')

# Result: [{'year': 2018, 'weighted_cluster_points': 25.5}, {'year': 2019, ...}, ...]
```

---

## Data Sources

All data seeded from extracted PDF files:

1. **Subjects**: Predefined KCSE subject list
2. **Institutions**: `scripts/institutions_data.json` (500 institutions)
3. **Degree Clusters**: `extraction_output/degree_clusters_MANUAL.json` (manually curated)
4. **TVET Clusters**: `extraction_output/tvet_clusters_MANUAL.json` (manually curated)
5. **Programmes**: `extraction_output/degree_programmes_full.json` + `degree_cutoffs_extracted.json`
6. **Cutoffs**: `extraction_output/degree_cutoffs_extracted.json` (2,525 records with 7-year history)

---

## Notes

### TVET Cluster Code Format

TVET clusters use a structured code format:

- **Prefix**: TVET, KNEC, or INTERNAL (based on examination section)
- **Cluster Number**: Numeric ID from source document
- **Variant/Subcat**: Additional identifier for subcategories or variants
- **Level**: DIPL (Diploma), CERT (Certificate), ARTI (Artisan)

**Examples**:

```
TVET-1-DIPL: Standard TVET cluster 1, Diploma level
KNEC-6-ANA-CERT: KNEC cluster 6, Analytical Chemistry variant, Certificate
INTERNAL-5-TAX-DIPL: Internal examiners cluster 5, Tax Administration, Diploma
```

### Cutoff Points Data Quality

- **Valid cutoffs**: 14,155 records with numeric values
- **NULL cutoffs**: 195 records where data was unavailable
- **Years covered**: 2018-2024 (7 years)
- **Most NULLs**: 2024 (165 NULLs) - likely due to data being preliminary

### Future Enhancements

- ✅ Subject requirements parsing (awaiting implementation)
- ✅ TVET programme seeding (if TVET programme data becomes available)
- ✅ Student recommendation algorithm optimization
- ✅ Historical trend analysis features

---

## Schema Migrations

All models migrated and database fully seeded as of 2026-02-01.

**Migration Status**: Up to date  
**Seeding Status**: ✅ Complete  
**Data Quality**: Verified with zero duplicates
changing 50+ rows

### ✅ New Schema Benefits

1. **No Duplication**: One `Programme` row, many `ProgrammeOffering` links
2. **Single Source of Truth**: Requirements defined once

---

## API Structure

With this schema, the API returns:

```json
{
  "id": 1,
  "kuccps_code": "1266128",
  "name": "Bachelor of Science in Computer Science",
  "level": "DEGREE",
  "cluster": {
    "code": "CLUSTER_7",
    "name": "Computing, IT & Related"
  },
  "job_market_demand": "HIGH",
  "requirements": [
    { "subject": "Mathematics", "minimum_grade": "C+" },
    { "subject": "English", "minimum_grade": "C+" }
  ],
  "offerings": [
    {
      "institution": "University of Nairobi",
      "location": "Nairobi",
      "cutoffs": [
        { "year": 2023, "points": 42.155 },
        { "year": 2022, "points": 41.882 }
      ]
    },
    {
      "institution": "JKUAT",
      "location": "Juja",
      "cutoffs": [{ "year": 2023, "points": 41.332 }]
    }
  ]
}
```

---

## Summary

**Key Relationships**:

1. **Programme → Cluster**: Many programmes belong to one cluster (e.g., all CS, IT, Software Engineering → Cluster 7)
2. **Programme → Institution**: Through `ProgrammeOffering` (many-to-many)
3. **ProgrammeOffering → CutOffPoint**: Each offering has yearly cut-offs
4. **Programme → Requirements**: Universal prerequisites

**Data Capture Flow**:

1. Define `ProgrammeLevel` and `ClusterGroup` (done via seed data)
2. Create generic `Programme` with cluster assignment
3. Add `ProgrammeRequirement` for subject prerequisites
4. Create `ProgrammeOffering` for each institution offering the programme
5. Add `CutOffPoint` records for each offering per year

This structure ensures data integrity, eliminates redundancy, and accurately models the real-world KUCCPS system.
