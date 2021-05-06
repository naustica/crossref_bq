SELECT cr_derived.*, cr_reference.reference
FROM `api-project-764811344545.cr_instant.cr_feb21_derived_2013_jn` AS cr_derived
LEFT OUTER JOIN (SELECT doi, reference
                 FROM (
                    SELECT y.doi,
                           ARRAY_AGG(STRUCT(rec.key,
                                            rec.doi,
                                            rec.doi_asserted_by,
                                            rec.journal_title)) AS reference,
                    FROM `api-project-764811344545.cr_instant.cr_feb21_complete` AS y
                    LEFT JOIN UNNEST(reference) AS rec
                    GROUP BY doi
                  )) AS cr_reference
ON cr_derived.doi = cr_reference.doi
