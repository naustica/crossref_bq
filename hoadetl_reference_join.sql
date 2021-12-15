SELECT cr_derived.*, cr_reference.reference
FROM `subugoe-collaborative.cr_instant.snapshot` AS cr_derived
LEFT OUTER JOIN (SELECT doi, reference
                 FROM (
                    SELECT y.doi,
                           ARRAY_AGG(STRUCT(rec.key,
                                            rec.doi,
                                            rec.doi_asserted_by,
                                            rec.unstructured,
                                            rec.journal_title)) AS reference,
                    FROM `subugoe-collaborative.cr_instant.snapshot_complete` AS y
                    LEFT JOIN UNNEST(reference) AS rec
                    GROUP BY doi
                  )) AS cr_reference
ON cr_derived.doi = cr_reference.doi
