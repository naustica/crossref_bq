# Workflow for Processing and Loading Crossref snapshots into Google BigQuery

In the context of scholarly communication analysis, crossref snapshots are regularly processed at the SUB Göttingen. This repository contains instructions on how to extract and transform crossref data for data analysis with Google BigQuery. Our workflow adapts the approach of [the academic observatory](https://github.com/The-Academic-Observatory/observatory-platform).

## Requirements

The following packages are required for this workflow.

- [Python3](https://www.python.org)
  - [requests](https://docs.python-requests.org/en/master/)
  - [gsutil](https://pypi.org/project/gsutil/)
- [mawk](https://invisible-island.net/mawk/)
- [pigz](https://linux.die.net/man/1/pigz)

## Setting Crossref Variables

Replace the following placeholders with your credentials.

```bash
CROSSREF_PLUS_API_TOKEN=YOUR_TOKEN
CROSSREF_MAILTO=YOUR_EMAIL
```

## Downloading Snapshot

We can use the official Crossref REST-API to download snapshots to our computer.

```bash
$ wget --header "Crossref-Plus-API-Token: Bearer ${CROSSREF_PLUS_API_TOKEN}" \
    https://api.crossref.org/snapshots/monthly/2021/04/all.json.tar.gz&mailto=${CROSSREF_MAILTO}
```

With the python module `crossref_bq`, which is stored in this repo, it is possible to check if a specific snapshot exists. Also, the module provides a method for downloading a snapshot.

```python
from crossref_bq.crossref_dump import CrossrefSnapshot

cr_dump = CrossrefSnapshot(year=2021, month=4)
if cr_dump.exists():
  cr_dump.download()
```

To download the last published snapshot, this script can also be used.

```bash
sh cr_snapshots_download.sh
```

## Data transformation

After the snapshot has been downloaded, we can start processing the dump. The `script cr_hpc.sh` consists of two parts, the second part is optional. In the first step a python script is started which extracts all compressed files in the downloaded snapshot and stores them in the folder `/extract` (folder can be specified). Next, the extracted files are transformed so that they can be read by Google BigQuery. For example, hyphens are transformed into underscores. Additionally, the JSON files are transformed into Newline-delimited JSON (BigQuery does not work with regular JSON). Transformed files are stored in the folder `/transform`. Currently, a Crossref snapshot consists of approximately 40,000 compressed JSON files (about 100GB).

The `CrossrefSnapshot` class takes the following parameters:

- `year` (publication year of the snapshot)
- `month` (publication month of the snapshot)
- `download_path` (file path to download the snapshot)
- `extract_path` (file path to extract the snapshot)
- `transform_path` (file path to transform the snapshot)

The second and optional step involves recompressing the transformed files. This reduces about 2/3 of the space taken.

This workflow was carried out with the help of the High Performance Computing-System of the [GWDG Göttingen](https://www.gwdg.de/web/guest). The HPC provides high-performance computers for employees of the university of Göttingen, which can be used for intensive computer tasks. To speed up data processing, the Python script uses parallelization. In this case, 16 CPU cores were obtained.

Starting a job on the HPC-System:

```bash
sbatch cr_hpc.sh
```

Step 1 (duration: ~8h):

```python
from crossref_bq.crossref_dump import CrossrefSnapshot

cr_dump = CrossrefSnapshot(year=2021,
                           month=4,
                           filename='all.json.tar.gz',
                           download_path='/scratch/users/haupka')

cr_dump.extract()
cr_dump.transform_release()
```

Step 2 (duration: ~34h):

```bash
cd /scratch/users/haupka/transform && ls -1 * | xargs -P 16 gzip
```

## Uploading Files to Google Bucket

Upload to Google Cloud Storage:

```bash
gsutil -m cp -r /scratch/users/haupka/transform/ gs://oadoi_full
```

## Creating a BigQuery Table

Load into BigQuery:

```bash
bq load
  --ignore_unknown_values
  --source_format=NEWLINE_DELIMITED_JSON
  api-project-764811344545:cr_instant.cr_apr21_complete
  gs://oadoi_full/transform/*.gz cr_bq_schema.json
```

Applying date transformation on the existing table:

```sql
SELECT doi,
       issued
FROM (
     SELECT doi,
            DATE(CONCAT(CAST(issued.date_parts[SAFE_OFFSET(0)] AS STRING), "-",
                 COALESCE(CAST(issued.date_parts[SAFE_OFFSET(1)] AS STRING), "1"), "-",
                 COALESCE(CAST(issued.date_parts[SAFE_OFFSET(2)] AS STRING), "1"))) AS issued,
            type
     FROM `api-project-764811344545.cr_instant.cr_apr21_complete`
     WHERE type = "journal-article"
     )
WHERE issued >= "2013-01-01"
```

## Issues encountered


## To Do
- Tests
- Python implementation of BigQuery CRUD operations
- Improving automation
