# Diversio HRIS Import Preview

A small Django web application that previews an HRIS CSV before employee
or reporting data is persisted. It parses and validates the upload,
resolves manager relationships, identifies root employees, and detects
reporting cycles.

## Project Overview

The application allows a user to:

-   Upload an HRIS CSV from the browser.
-   See the total number of source rows.
-   See accepted employees.
-   See row-level validation errors with source row numbers.
-   See root employees with no manager.
-   See managers and their direct-report counts.
-   See employees that participate in reporting cycles.

The upload is analyzed in memory; database persistence is not required.

## Tech Stack

-   Python
-   Django
-   Python `csv` module
-   Django templates / HTML / CSS
-   Django `SimpleTestCase`

## How to Run Locally

### 1. Install dependencies

Create and activate a virtual environment if desired, then install
Django:

``` bash
python3 -m venv venv
source venv/bin/activate
pip install django
```

### 2. Start the development server

``` bash
python3 manage.py runserver
```

Open the local URL shown by Django in your browser and upload a CSV
file.

## How to Run Tests

``` bash
python3 manage.py test preview
```

The current test suite contains 8 focused tests covering duplicate
identity handling, reporting cycles, manager-error row numbers,
blank-line row numbering, incomplete rows, malformed CSV rows, and
quoted CSV values.

## CSV Format

The expected CSV contains these headers, in any order:

``` text
employee_id,employee_name,email,manager_id,manager_email,department
```

Example:

``` csv
employee_id,employee_name,email,manager_id,manager_email,department
1,Alice,alice@company.com,,,Engineering
2,Bob,bob@company.com,1,,Engineering
3,"Smith, Jane",jane@company.com,,alice@company.com,Product
```

Quoted values containing commas are supported. UTF-8 files with or
without a byte-order mark (BOM) are supported.

## Validation Rules

### Employee Identity

-   `employee_id` and `email` are required.
-   Surrounding whitespace is trimmed from values.
-   `email` and `manager_email` are normalized to lowercase.
-   Employee IDs remain case-sensitive.
-   Duplicate employee IDs are rejected.
-   Duplicate emails are rejected.
-   Invalid identity rows do not participate in manager lookup or
    hierarchy analysis.

### Malformed CSV

Rows whose field count does not match the CSV header are rejected with a
clear malformed-row error instead of causing an unhandled exception.

## Manager Resolution Rules

Manager rows may appear before or after their reports.

1.  Both manager fields blank: the employee is a root.
2.  Only `manager_id` supplied: resolve the manager by employee ID.
3.  Only `manager_email` supplied: resolve the manager by normalized
    email.
4.  Both supplied: both references must identify the same employee.
5.  Missing managers, conflicting references, and self-management
    produce validation errors.
6.  An employee with a manager error remains an accepted employee but
    does not produce a reporting relationship and is not a root.

## Reporting Cycle Detection

The application identifies employees that actually participate in a
reporting cycle. An employee who only reports into a cycle is not
classified as a cycle member.

## Complexity

The implementation uses dictionaries for identity and manager lookups
and graph traversal for cycle detection.

-   **Time:** `O(N)`
-   **Space:** `O(N)`

where `N` is the number of source employee rows.

## Important Assumptions

-   The uploaded file follows the required HRIS CSV structure.
-   Employee IDs are case-sensitive.
-   Email addresses are compared case-insensitively after normalization.
-   Invalid identity rows are excluded from hierarchy analysis.
-   Reporting relationships are created only when manager resolution
    succeeds.
-   The application is an import preview and does not persist employee
    data.
-   A row whose field count differs from the header is treated as
    malformed.

## Known Limitations

-   This is an import-preview application, not a production HRIS
    ingestion system.
-   No authentication or user-account system is included.
-   No production deployment configuration is included.
-   Employee or relationship data is not persisted to a database.
-   The frontend intentionally uses plain HTML/CSS rather than a
    JavaScript framework.
-   Rows with a field count different from the header are treated as
    malformed.

## AI Tools Used

AI tools were used as development and review assistants during the
assignment, including ChatGPT, Gemini, and Claude. They were used for
implementation guidance, code review, edge-case analysis, test
suggestions, debugging support, and final review.

AI-generated suggestions were reviewed, tested, and adjusted before
being included in the project.

## Approximate Time Spent

Approximately **24+ hours** were spent across implementation, debugging,
testing, edge-case verification, UI review, and final review. The
recording time is excluded from this estimate.

## Out of Scope

The following were intentionally not implemented because they were
outside the assignment scope:

-   Authentication or user accounts.
-   Production deployment.
-   Database persistence.
-   A JavaScript frontend framework.
-   Elaborate styling.
-   Features unrelated to the import preview.

## Video Walkthrough

The assignment requires a narrated screen recording of no more than 10
minutes covering the working application, key code paths, tests, an
important edge case/trade-off, and AI-tool usage.
