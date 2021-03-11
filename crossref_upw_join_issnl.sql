SELECT cr.*, upw.journal_issn_l
FROM `crossref.cr_jan21` AS cr
LEFT OUTER JOIN `oadoi_full.upw_Feb21_08_21` AS upw
ON cr.doi = upw.doi
