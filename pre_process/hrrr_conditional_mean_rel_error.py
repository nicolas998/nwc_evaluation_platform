import pandas as pd 
import pylab as pl 
import netCDF4
import numpy.ma as ma
import numpy as np 

year = 2019
rmin = 4
prod = 'nwcup'

#re = netCDF4.Dataset('/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error.nc' % year)
usgs = pd.read_csv('../data/usgs_joined_rlf.csv', index_col=0)
if prod == 'nwc' or prod == 'per':
    nwc_up = netCDF4.Dataset('../data/%d_nwc_error.nc' % year)
else:
    nwc_up = netCDF4.Dataset('../data/%d_nwc_error_upsegment.nc' % year)
data = np.load('../data/hrrr_basin_'+str(year)+'.npz', allow_pickle = True)
hrrr_totals = data['data']
hrrr_usgs = data['usgs_id']
hrrr_areas = pd.read_csv('../data/hrrr_usgs_areas.csv', index_col = 0)
hrrr_rain = np.divide(hrrr_totals, hrrr_areas.values)
shared = np.isin(hrrr_usgs, nwc_up['usgs_id']).nonzero()[0]

def compute_mean_rel_error(lead, nwc_data,prod,rcond = 0):
    me = []    
    _nwc = nwc_data[prod][:,lead,:]
    _nwc[_nwc.data <= -999] = ma.masked        
    a = ma.copy(_nwc)
    a[hrrr_rain[shared] < rcond] = ma.masked
    me.append(a.mean(axis = 1).data)
    me.append(np.abs(a).mean(axis = 1).data)
    ll = lead + 1 
    me = pd.DataFrame(np.array(me).T, index=nwc_data['usgs_id'][:], columns=['me_%d'%ll,'ame_%d'%ll])
    idx = usgs.index.intersection(me.index)
    return me 

if len(prod) == 3:
    prod2eval = 'er_%s' % prod
else:
    prod2eval = 'er_%s' % prod[:3]
for rmin in [3,]:
    me = []
    for lead in range(18):    
        me.append(compute_mean_rel_error(lead,nwc_up,prod2eval, rmin))
        lname = lead + 1
        #me.to_pickle('../data/%d_lead_%d_nwcup_mean_rel_error_uncond.gz' % (year, lname))
        print(lead)
    me = pd.concat(me, axis = 1)
    me.to_pickle('../data/%d_%s_mean_rel_error_hrrr_%d.gz' % (year,prod, rmin))
    
nwc_up.close()