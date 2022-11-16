import pandas as pd 
import pylab as pl 
import netCDF4
import numpy.ma as ma
import numpy as np 

def compute_mean_rel_error(lead, nwc_data,prod,qcond = 0):
    me = []    
    _nwc = nwc_data[prod][:,lead,:]
    _nwc[_nwc.data <= -999] = ma.masked        
    me.append(_nwc.mean(axis = 1).data)
    me.append(np.abs(_nwc).mean(axis = 1).data)
    ll = lead + 1 
    me = pd.DataFrame(np.array(me).T, index=nwc_data['usgs_id'][:], columns=['me_%d'%ll,'ame_%d'%ll])
    idx = usgs.index.intersection(me.index)
    return me 

for year in [2019,2020,2021]:
    print(year)
    for prod in ['nwc','per']:

    #re = netCDF4.Dataset('/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error.nc' % year)
        usgs = pd.read_csv('../data/usgs_joined_rlf.csv', index_col=0)
        if prod == 'nwc' or prod == 'per':
            nwc_up = netCDF4.Dataset('../source/%d_nwc_error.nc' % year)
            #nwc_up = netCDF4.Dataset('/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error.nc' % year)
        else:
            nwc_up = netCDF4.Dataset('../data/%d_nwc_error_upsegment.nc' % year)
            #nwc_up = netCDF4.Dataset('/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error_upsegment.nc' % year)

        if len(prod) == 3:
            prod2eval = 'er_%s' % prod
        else:
            prod2eval = 'er_%s' % prod[:3]

        me = []
        for lead in range(18):
            me.append(compute_mean_rel_error(lead,nwc_up,prod2eval))
            lname = lead + 1
            #me.to_pickle('../data/%d_lead_%d_nwcup_mean_rel_error_uncond.gz' % (year, lname))
            print(lead)
        me = pd.concat(me, axis = 1)
        me.to_pickle('../data/%d_%s_mean_rel_error_uncond.gz' % (year, prod))
        nwc_up.close()
        
        print(prod)
    