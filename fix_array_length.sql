SELECT publisher,
       title,
       abstract,
       reference_count,
       is_referenced_by_count,
       y.doi,
       member,
       created,
       deposited,
       indexed,
       issued,
       posted,
       accepted,
       container_title,
       issue,
       volume,
       page,
       article_number,
       published_print,
       published_online,
       issn,
       archive,
       CASE
        WHEN (ANY_VALUE(lic.start) IS NULL AND ANY_VALUE(lic.url) IS NULL AND ANY_VALUE(lic.delay_in_days) IS NULL AND ANY_VALUE(lic.content_version) IS NULL)
        THEN NULL
        ELSE ANY_VALUE(license)
       END AS license,
       CASE
        WHEN (ANY_VALUE(fun.name) IS NULL AND ANY_VALUE(fun.doi) IS NULL AND ANY_VALUE(fun.award) IS NULL AND ANY_VALUE(fun.doi_asserted_by) IS NULL)
        THEN NULL
        ELSE ANY_VALUE(funder)
       END AS funder,
       CASE
        WHEN (ANY_VALUE(lin.url) IS NULL AND ANY_VALUE(lin.content_type) IS NULL AND ANY_VALUE(lin.content_version) IS NULL AND ANY_VALUE(lin.intended_application) IS NULL)
        THEN NULL
        ELSE ANY_VALUE(link)
       END AS link,
       ANY_VALUE(relation) AS relation,
       CASE
        WHEN (ANY_VALUE(aut.family) IS NULL AND ANY_VALUE(aut.given) IS NULL AND ANY_VALUE(aut.ORCID) IS NULL AND ANY_VALUE(aut.authenticated_orcid) IS NULL)
        THEN NULL
        ELSE ANY_VALUE(author)
       END AS author,
       CASE
        WHEN (ANY_VALUE(rec.key) IS NULL AND ANY_VALUE(rec.doi) IS NULL AND ANY_VALUE(rec.doi_asserted_by) IS NULL AND ANY_VALUE(rec.unstructured) IS NULL AND ANY_VALUE(rec.journal_title) IS NULL)
        THEN NULL
        ELSE ANY_VALUE(reference)
       END AS reference,
FROM `subugoe-collaborative.cr_instant.snapshot` AS y,
    UNNEST(license) AS lic,
    UNNEST(funder) AS fun,
    UNNEST(link) AS lin,
    UNNEST (author) AS aut,
    UNNEST(reference) AS rec
GROUP BY publisher,
       title,
       abstract,
       reference_count,
       is_referenced_by_count,
       doi,
       member,
       created,
       deposited,
       indexed,
       issued,
       posted,
       accepted,
       container_title,
       issue,
       volume,
       page,
       article_number,
       published_print,
       published_online,
       issn,
       archive
