# Workflow for Processing and Loading Crossref snapshots into Google BigQuery

This repository contains instructions on how to extract and transform Crossref data for data analysis with Google BigQuery. This workflow adapts the approach of [the academic observatory](https://github.com/The-Academic-Observatory/observatory-platform).

## Requirements

The following packages are required for this workflow.

- [Python3](https://www.python.org)
  - [gsutil](https://pypi.org/project/gsutil/)
  - [json-lines](https://pypi.org/project/json-lines/)

## Setting Crossref Variables

Replace the following placeholders with your credentials.

```bash
$ CROSSREF_PLUS_API_TOKEN=YOUR_TOKEN
$ CROSSREF_MAILTO=YOUR_EMAIL
```

## Download Snapshot

```bash
$ sh cr_snapshots_download.sh
```

## Data transformation

This workflow has been tested using the High Performance Computing-System of the [GWDG Göttingen](https://www.gwdg.de/web/guest). The HPC provides high-performance computers for employees of the University of Göttingen, which can be used for intensive computing tasks. To speed up data processing, the Python script uses parallelization. In this case, 16 CPU cores were obtained.

Starting a job on the HPC-System:

```bash
$ sbatch cr_hpc.sh
```


## Uploading Files to Google Bucket

Upload to Google Cloud Storage:

```bash
$ gsutil -m cp -r /scratch/users/haupka/transform/ gs://bigschol
```

## Creating a BigQuery Table

Load into BigQuery:

```bash
$ bq load
  --ignore_unknown_values
  --source_format=NEWLINE_DELIMITED_JSON
  --clustering_fields=type
  subugoe-collaborative:cr_instant.snapshot
  gs://bigschol/transform/*.gz schema_crossref.json
```

## Example Query

```sql
SELECT member, publisher, COUNT(DISTINCT(doi)) as n
FROM `subugoe-collaborative.cr_instant.snapshot` 
GROUP BY member, publisher
ORDER BY n DESC
LIMIT 10
```

| member | publisher                                 | n        |
|--------|-------------------------------------------|----------|
| 78     | Elsevier BV                               | 22023208 |
| 311    | Wiley                                     | 11428895 |
| 297    | Springer Science and Business Media LLC   | 10721803 |
| 286    | Oxford University Press (OUP)             | 5383878  |
| 301    | Informa UK Limited                        | 5144680  |
| 340    | Public Library of Science (PLoS)          | 4530155  |
| 263    | IEEE                                      | 4510396  |
| 179    | SAGE Publications                         | 3061413  |
| 276    | Ovid Technologies (Wolters Kluwer Health) | 2838793  |
| 316    | American Chemical Society (ACS)           | 2720944  |

## To Do
- Tests
- Python implementation of BigQuery CRUD operations
- Improving automation
