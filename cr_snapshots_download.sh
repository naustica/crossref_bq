wget --header "Crossref-Plus-API-Token: Bearer ${CROSSREF_PLUS_API_TOKEN}" \
    https://api.crossref.org/snapshots/monthly/latest/all.json.tar.gz&mailto=${CROSSREF_MAILTO}
