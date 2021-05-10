#!/bin/bash
#SBATCH -p medium
#SBATCH -C scratch
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -t 40:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nick.haupka@sub.uni-goettingen.de



module load jq/1.6


tar tzf /scratch/users/haupka/all.json.tar.gz | while IFS= read -r f ; do
    tar Oxzf /scratch/users/haupka/all.json.tar.gz "$f" | jq -c '.items[]' | parallel --pipe --block 100M --jobs 16 --files --tmpdir /scratch/users/haupka/cr_export --recend '}\n' "jq -c 'select(.type == \"journal-article\") | select( .issued[\"date-parts\"][][] | select(length >= 4) | . > 2007) | {doi: .DOI, title: .title[0], issued: [ try (.issued[\"date-parts\"][] | join(\"-\") ) catch null ] | .[], issued_year: .issued[\"date-parts\"][][] | select(length >= 1000) | ., created: .created | .timestamp, published_print: [ try (.[\"published-print\"][\"date-parts\"][] | join(\"-\")) catch null] | .[], published_online: [ try (.[\"published-online\"][\"date-parts\"][] | join(\"-\")) catch null] | .[], page, link: [try .link[] catch {URL: null, \"content-type\": null, \"content-version\": null, \"intended-application\": null} | {url: .URL, content_type: .[\"content-type\"], content_version: .[\"content-version\"], intended_application: .[\"intended-application\"]}], license: [try .license[] catch {URL: null, start: null, \"delay-in-days\": null, \"content-version\": null} | {url: .URL, date: .start | .timestamp, delay_in_days: .[\"delay-in-days\"], content_version: .[\"content-version\"]}], container_title: .[\"container-title\"][0], publisher, member, issn: .ISSN | [try join(\", \") catch null] | .[], reference_count: .[\"reference-count\"], is_referenced_by_count: .[\"is-referenced-by-count\"], indexed: .indexed | .timestamp}'"

    if [ "$f" = "./" ]; then
        break
    fi
done


for file in /scratch/users/haupka/cr_export/*.par
do
  mv "$file" "${file%.par}.jsonl"
done

gzip -r /scratch/users/haupka/cr_export
