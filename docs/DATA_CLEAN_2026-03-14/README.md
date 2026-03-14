# tzfpy's PyPI Download Statistics

[`script_job_6a7f35f7e60dc30855f818b6187f836a_0.csv`](./script_job_6a7f35f7e60dc30855f818b6187f836a_0.csv):

```sql
DECLARE package_name STRING DEFAULT 'tzfpy';
DECLARE end_date DATE DEFAULT DATE '2026-03-13';
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 30 DAY);

SELECT
  file.version AS version,
  file.filename AS filename,
  COUNT(*) AS downloads_30d
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project = package_name
  AND DATE(timestamp) BETWEEN start_date AND end_date
  AND details.installer.name = 'pip'
GROUP BY version, filename
ORDER BY downloads_30d DESC, version, filename;
```

[`script_job_b7dcfb358f517da711bbf729a784c521_0.csv`](./script_job_b7dcfb358f517da711bbf729a784c521_0.csv)

```sql
DECLARE package_name STRING DEFAULT 'tzfpy';
DECLARE end_date DATE DEFAULT DATE '2026-03-13';
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 30 DAY);

SELECT
  file.version AS version,
  file.filename AS filename,
  COUNT(*) AS downloads_30d
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project = package_name
  AND DATE(timestamp) BETWEEN start_date AND end_date
  AND details.installer.name = 'uv'
GROUP BY version, filename
ORDER BY downloads_30d DESC, version, filename;
```

[`script_job_5c3854808754dd3102806a757c45cf6f_0.csv`](./script_job_5c3854808754dd3102806a757c45cf6f_0.csv)

```sql
DECLARE package_name STRING DEFAULT 'tzfpy';
DECLARE end_date DATE DEFAULT DATE '2026-03-13';
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 30 DAY);

SELECT
  file.version AS version,
  file.filename AS filename,
  COUNT(*) AS downloads_30d
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project = package_name
  AND DATE(timestamp) BETWEEN start_date AND end_date
GROUP BY version, filename
ORDER BY downloads_30d DESC, version, filename;
```

[`pypi_all_files.csv`](./pypi_all_files.csv), all files in PyPI.

[`cleanup_ranked_list.csv`](./cleanup_ranked_list.csv), ranked list of files.
