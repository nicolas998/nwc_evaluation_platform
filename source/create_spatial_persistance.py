import numpy as np 
import argparse
import pandas as pd 
import netCDF4



def get_parent_flow(usgs_id, year):
    #Get the list of parents from the csv 
    a = usgs_p.loc[usgs_id, 'from_usgs']
    parents = np.array(a[1:-1].split(','))
    
    #Get the flow data from the parents
    flow_parents = []
    existing_childs = []
    for parent in parents:
        try:
            qo = np.load('/mnt/y/flow/USGS_observed/%d/%d_usgs_%s.npz' % (year, year,parent))
            uxt_u = np.unique(qo['data']['uxt'])
            #Converts the observed flow to match the nwc forecast
            flow_o = np.ones(d.dimensions['issue_time'].size)*-999
            shared1 = np.argwhere(np.in1d(uxt, uxt_u)).T[0]
            shared2 = np.argwhere(np.in1d(uxt_u, uxt)).T[0]
            flow_o[shared1] = qo['data']['val'][shared2]*0.028
            flow_o[flow_o <= 0] = np.nan
            flow_parents.append(flow_o)
            existing_childs.append(parent)
        except:
            pass
    flow_parents = np.array(flow_parents)
    parents_sum = flow_parents.sum(axis = 0)
    
    qo = np.load('/mnt/y/flow/USGS_observed/%d/%d_usgs_%s.npz' % (year, year,usgs_id))
    uxt_u = np.unique(qo['data']['uxt'])
    #Converts the observed flow to match the nwc forecast
    flow_o = np.ones(d.dimensions['issue_time'].size)*-999
    shared1 = np.argwhere(np.in1d(uxt, uxt_u)).T[0]
    shared2 = np.argwhere(np.in1d(uxt_u, uxt)).T[0]
    flow_o[shared1] = qo['data']['val'][shared2]*0.028
    flow_o[flow_o <= 0] = np.nan
    
    flow_scaled = np.nanmean(flow_o) * (parents_sum / np.nanmean(parents_sum))
    
    #Computes the errors of using the persistence 
    Ep = []
    Es = []
    for lead in range(1,19):
        a = 100*(parents_sum-np.roll(flow_o,lead))/np.roll(flow_o,lead)
        Ep.append(a.astype(int))
        a = 100*(flow_scaled-np.roll(flow_o,lead))/np.roll(flow_o,lead)
        Es.append(a.astype(int))
    
    results = {
        'childs': existing_childs,
        'flow': flow_o,
        'flow_childs':flow_parents,
        'sum_childs':parents_sum,
        'scaled_childs': flow_scaled,
        'er_chi': Ep,
        'er_sca': Es
    }
    
    return results

year = 2019

usgs_p = pd.read_csv('../data/usgs_parents.csv', usecols=[1,4],dtype = {'to_usgs':str,'from_usgs':'str'}, index_col=0)
d = netCDF4.Dataset('/mnt/y/flow/NWC_forecast/%d_nwc_short_upsegment.nc' % year)
usgs = d['usgs_id'][:]
uxt = d['issue_time'][:]


if __name__ == "__main__":

    #Sets the netCDf with the results
    print('Creating')
    root = netCDF4.Dataset('%d_spatial_per_simple.nc' % year, 'w', format = 'NETCDF4')
    root.createDimension('station', usgs_p.shape[0])
    root.createDimension('lead_time', 18)
    root.createDimension('issue_time', d.dimensions['issue_time'].size)
    #Variables 
    usgs_codes = root.createVariable('usgs_id', np.str, ('station',))
    lead_time = root.createVariable('lead_time', np.ubyte, ('lead_time', ))
    issue_time = root.createVariable('issue_time', int, ('issue_time', ))
    per_simple = root.createVariable('per_simple', int, ('station', 'issue_time'), chunksizes=(1, d.dimensions['issue_time'].size), zlib=True)
    per_scaled = root.createVariable('per_scaled', int, ('station', 'issue_time'), chunksizes=(1, d.dimensions['issue_time'].size), zlib=True)
    error_simple = root.createVariable('er_child', int, ('station', 'lead_time', 'issue_time'), chunksizes=(1, 1, d.dimensions['issue_time'].size), zlib=True)
    error_scaled = root.createVariable('er_child_sca', int, ('station', 'lead_time', 'issue_time'), chunksizes=(1, 1, d.dimensions['issue_time'].size), zlib=True)
    #Variable units
    issue_time.units = 'second'
    per_simple.units = '100cms'
    lead_time.units = 'hour'
    per_scaled.units = '100cms'
    #Assign data values
    usgs_codes[:] = usgs_p.index.values
    issue_time[:] = d['issue_time'][:]
    lead_time[:] = [i for i in range(1, 19, 1)]
    per_simple[:,:] = np.zeros(
            (usgs_p.shape[0],d['issue_time'].shape[0]),
            dtype=np.int32
        ) - 99999
    per_scaled[:,:] = np.zeros(
            (usgs_p.shape[0],d['issue_time'].shape[0]),
            dtype=np.int32
        ) - 99999
    error_simple[:,:,:] = np.zeros(
            (usgs_p.shape[0],18,d['issue_time'].shape[0]),
            dtype=np.int32
        ) - 99999
    error_scaled[:,:,:] = np.zeros(
            (usgs_p.shape[0],18,d['issue_time'].shape[0]),
            dtype=np.int32
        ) - 99999
    print('netcdf created')

    real_childs = {}
    for pos, gauge in enumerate(usgs_p.index.values[:10]):
        try:
            childs = get_parent_flow(gauge, year)
            error_simple[pos,:,:] = childs['er_chi']
            error_scaled[pos,:,:] = childs['er_sca']
            per_simple[pos,:] = childs['sum_childs']*100
            per_scaled[pos,:] = childs['scaled_childs']*100
            real_childs.update({gauge:childs['childs']})
            real_childs[gauge] = '{' +','.join(real_childs[gauge]) + '}'
            print(pos, usgs[pos], 0)
        except:
            print(pos, usgs[pos], 1)
    
    #Writes the fiule with the current childs of each gauge (the ones that have records)
    f = open('../data/usgs_actual_parents_%d.csv' % year,'w')
    f.write('to_usgs, from_usgs\n')
    for i in c.keys():
        f.write('%s, "%s"\n' % (i, c[i]))
    f.close()

    #Close the netCDF files
    d.close()
    root.close()