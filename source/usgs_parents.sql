with pre as (SELECT 
                to_usgs, to_comid,          
                array_agg(from_comid) from_comid,
                array_agg(from_usgs) from_usgs  
FROM nhd_plus_21.fix_usgs_connect 
--- WHERE to_usgs = '02465000'
WHERE to_comid is not null 
GROUP BY to_usgs, to_comid)

SELECT cardinality(from_comid) cnt, * FROM pre order by cardinality(from_comid) DESC