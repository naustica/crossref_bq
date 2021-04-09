from crossref_bq.crossref_dump import CrossrefSnapshot

cr = CrossrefSnapshot(year=2021, month=2, filename='all.json.tar.gz', download_path='/scratch/users/haupka')

cr.extract()
cr.transform_release()
