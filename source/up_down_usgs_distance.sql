WITH pre as (
SELECT 0 rn, 8212809 comid UNION
SELECT ROW_NUMBER() OVER () rn, path_to_outlet as comid FROM nhd_plus_21.path_to_outlet(8212809))

SELECT  
	pre.*, 
	lengthkm,
	sum(lengthkm) over (order by rn),
	ffa.divergence,	
	ff.to_comid,
	(	
	SELECT 
		count(*)
	FROM 
		nhd_plus_21.flow_attr_plus L 
	INNER JOIN 
		nhd_plus_21.flow_attr_plus R ON (l.from_comid = r.to_comid)
	WHERE 
		L.from_comid = pre.comid AND 
		R.FROM_comid in (SELECT P.comid FROM nhd_plus_21.usgs_path P)
	)
FROM 
	pre 
inner join 
	nhd_plus_21.flow_attr ffa using (comid)	
LEFT JOIN 
	nhd_plus_21.flow_attr_plus as ff on (comid = from_comid) 
WHERE ff.divergence < 2