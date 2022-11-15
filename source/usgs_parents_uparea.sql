with pre as (SELECT 
	to_usgs, 
 	to_comid,
	sum(totdasqkm) direct_descendants_uparea		 
FROM 
	nhd_plus_21.fix_usgs_connect 
INNER JOIN 
	nhd_plus_21.usgs_comid on (com_id = from_comid)   
GROUP BY to_usgs, to_comid)

SELECT *,  (SELECT totdasqkm FROM nhd_plus_21.usgs_comid WHERE com_id = to_comid ) from pre