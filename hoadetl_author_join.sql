SELECT cr_derived.*, cr_author.author
FROM `api-project-764811344545.cr_instant.cr_feb21_derived_2013_jn` AS cr_derived
LEFT OUTER JOIN (SELECT doi, author
                 FROM (
                    SELECT doi,
                    ARRAY_AGG(STRUCT(aut.family,
                              aut.given,
                              aut.ORCID,
                              aut.authenticated_orcid,
                              aut.affiliation)) AS author
                    FROM `api-project-764811344545.cr_instant.cr_feb21_complete`
                    LEFT JOIN UNNEST(author) AS aut
                    GROUP BY doi
                  )) AS cr_author
ON cr_derived.doi = cr_author.doi
