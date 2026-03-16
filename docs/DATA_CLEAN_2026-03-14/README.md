# tzfpy's PyPI Download Statistics

Use one BigQuery query and keep installer granularity in one CSV:
[`script_job_81da1603e50b330166a12ee99b59069c_0.csv`](./script_job_81da1603e50b330166a12ee99b59069c_0.csv)

```sql
DECLARE package_name STRING DEFAULT 'tzfpy';
DECLARE end_date DATE DEFAULT DATE '2026-03-13';
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 30 DAY);

SELECT
  COALESCE(details.installer.name, 'unknown') AS installer,
  file.version AS version,
  file.filename AS filename,
  COUNT(*) AS downloads_30d
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project = package_name
  AND DATE(timestamp) BETWEEN start_date AND end_date
GROUP BY installer, version, filename
ORDER BY installer, downloads_30d DESC, version, filename;
```

`analyze_cleanup_candidates.py` now reads this installer-level CSV first, then derives:
- `downloads_all_30d` from sum of installers
- `downloads_pip_30d` from installer = `pip`
- `downloads_uv_30d` from installer = `uv`

[`pypi_all_files.csv`](./pypi_all_files.csv), all files in PyPI.

[`cleanup_ranked_list.csv`](./cleanup_ranked_list.csv), ranked list of files.
