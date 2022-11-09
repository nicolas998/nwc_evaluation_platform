import netCDF4 
import numpy as np 
import argparse

def compute_pers_nwc_dif(gage_pos, year):    
    #Read the gage position from the netCDf dataFrame and get its unix time
    qo = np.load('/mnt/y/flow/USGS_observed/%d/%d_usgs_%s.npz' % (year, year,usgs[gage_pos]))
    uxt_u = qo['data']['uxt']
    #Converts the observed flow to match the nwc forecast
    flow_o = np.ones(d.dimensions['issue_time'].size)*-999
    shared1 = np.argwhere(np.in1d(uxt, uxt_u)).T[0]
    shared2 = np.argwhere(np.in1d(uxt_u, uxt)).T[0]
    flow_o[shared1] = qo['data']['val'][shared2]*0.028
    flow_o[flow_o <= 0] = np.nan
    #Compute the differences 
    Es = []
    Ep = []
    for lead in range(1,19):
        flow_s = d['flow'][gage_pos,lead-1,:]/100
        flow_s[flow_s <= 0] = np.nan
        a = 100*(flow_s-np.roll(flow_o,lead))/np.roll(flow_o,lead)
        Es.append(a.astype(int))
        a = 100*(flow_o-np.roll(flow_o,lead))/np.roll(flow_o,lead)
        Ep.append(a.astype(int))
    return Es, Ep

if __name__ == "__main__":
    
    #Parse arguments
    parser = argparse.ArgumentParser(description='cmpute difference betwee usgs and nwc forecast')    
    parser.add_argument('year', type=int, help='id of the gauge')
    args = parser.parse_args()
    
    #Opens the necDF
    year = args.year
    d = netCDF4.Dataset('/mnt/y/flow/NWC_forecast/%d_nwc_short_upsegment.nc' % year)
    usgs = d['usgs_id'][:]
    uxt = d['issue_time'][:]
    
    #Sets the netCDf with the results
    print('Creating')
    root = netCDF4.Dataset('%d_nwc_error_upsegment.nc' % year, 'w', format = 'NETCDF4')
    root.createDimension('station', d.dimensions['station'].size)
    root.createDimension('lead_time', 18)
    root.createDimension('issue_time', d.dimensions['issue_time'].size)
    #Variables 
    usgs_codes = root.createVariable('usgs_id', np.str, ('station',))
    lead_time = root.createVariable('lead_time', np.ubyte, ('lead_time', ))
    issue_time = root.createVariable('issue_time', int, ('issue_time', ))
    error_nwc = root.createVariable('er_nwc', int, ('station', 'lead_time', 'issue_time'), chunksizes=(1, 1, d.dimensions['issue_time'].size), zlib=True)
    error_per = root.createVariable('er_per', int, ('station', 'lead_time', 'issue_time'), chunksizes=(1, 1, d.dimensions['issue_time'].size), zlib=True)
    #Variable units
    issue_time.units = 'second'
    lead_time.units = 'hour'
    error_nwc.units = 'adim'
    error_per.units = 'adim'
    #Assign data values
    usgs_codes[:] = d['usgs_id'][:]
    lead_time[:] = [i for i in range(1, 19, 1)]
    issue_time[:] = d['issue_time'][:]
    error_nwc[:,:,:] = np.zeros(
            d['flow'].shape,
            dtype=np.int32
        ) - 999
    error_per[:,:,:] = np.zeros(
            d['flow'].shape,
            dtype=np.int32
        ) - 999
    print('netcdf created')
    
    #Computes the errors 
    #Ess = np.zeros(d['flow'].shape) - 999
    #Epp = np.zeros(d['flow'].shape) - 999
    for pos in range(d['usgs_id'].shape[0]):
        try:
            Es, Ep = compute_pers_nwc_dif(pos, year)
            error_nwc[pos,:,:] = Es
            error_per[pos,:,:] = Ep
            print(pos, usgs[pos], 0)
        except:
            print(pos, usgs[pos], 1)
    
    #Close the netCDF files
    d.close()
    root.close()