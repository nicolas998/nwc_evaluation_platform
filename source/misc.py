import glob 
from datetime import date 
import pandas as pd 
import geopandas as gp 
import json
import glob 
#import plotly.express as px
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json 
import geopandas as gp 
import dash_bootstrap_components as dbc
from dash import html
from hydroeval import evaluator, kge, nse, pbias
import base64
import netCDF4 
import numpy.ma as ma
#Paths to the files
# path_netCDF = '/mnt/y/flow/NWC_forecast/%d_nwc_short.nc' 
# path_netCDF_up = '/mnt/y/flow/NWC_forecast/%d_nwc_short_upsegment.nc'
# path_netCDF_er = '/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error.nc' 
# path_netCDF_er_up = '/mnt/y/flow/NWC_persistence_rel_error/%d_nwc_error_up.nc' 

path_netCDF = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/%d_nwc_short.nc' 
path_netCDF_up = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/%d_nwc_short_upsegment.nc'
path_netCDF_er = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/%d_nwc_error.nc' 
path_netCDF_er_up = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/%d_nwc_error_up.nc' 

path_usgs = '/mnt/y/flow/USGS_observed/%d/'
path_usgs_meta = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/usgs_joined_rlf.csv'
path_local_data = '/mnt/c/Users/nicolas/Documents/2022_Witek_web/platform/data/'

plotly_colors = [
    '#000000', # Black
    '#d62728',  # brick red
    '#2ca02c',  # cooked asparagus green
    '#9467bd',  # muted purple
    '#ff7f0e',  # safety orange
    '#17becf'   # blue-teal
    '#bcbd22',  # curry yellow-green
    '#1f77b4',  # muted blue
    '#8c564b',  # chestnut brown
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray    
]

class misc:
    def __init__(self,year,usgs_id, region):        
        self.__load_netCDF__()
        self.__load_rlf__()
        self.__load_hrrr_cumulative_data__(year)
        #Reads the usgs metadata and keeps only the one in the records
        self.usgs = pd.read_csv(path_usgs_meta, index_col=0)
        self.usgs['area'] = self.usgs['area'] * 2.59
        self.usgs = self.usgs.loc[self.nwc_forecast_up[year]['usgs_id'][:]]        
        #Display control variables 
        self.active_tab = 'tab_flow'
        #Initialize options variables 
        self.__init_years_selector__()
        #Load the statistics of the error metrics 
        self.load_error_metrics(0)
        self.current_condition = 0
        #Status of the system
        self.current_usgs = usgs_id
        self.current_region = region
    
    def load_error_metrics(self, condition):
        if condition == 0:
            post = 'uncond.gz'
        else:
            post = 'hrrr_%d.gz' % condition
        self.current_condition = condition
        self.met_mu_error = {
            'up':{'mean':pd.read_pickle(path_local_data + '2019_nwcup_mean_rel_error_'+post)},
            'nwc':{'mean':pd.read_pickle(path_local_data + '2019_nwc_mean_rel_error_'+post)},
            'per':{'mean':pd.read_pickle(path_local_data + '2019_per_mean_rel_error_'+post)},
        }
    
    def __load_hrrr_cumulative_data__(self, year):
        data = np.load(path_local_data + 'hrrr_basin_'+str(year)+'.npz', allow_pickle = True)
        self.hrrr_usgs = data['usgs_id']
        self.hrrr_totals = data['data']
        self.hrrr_areas = pd.read_csv(path_local_data + 'hrrr_usgs_areas.csv', index_col = 0)
        
    def __load_rlf__(self):
        self.rlf_df = gp.read_file(path_local_data + 'rlf.geojson')        
        with open(path_local_data + 'rlf.geojson','r') as f:
            self.rlf_geojson = json.load(f)
    
    def __load_netCDF__(self):
        self.nwc_forecast = {}
        self.nwc_forecast_up = {}
        self.nwc_dates = {}
        self.nwc_uxt = {}
        for year in range(2019,2020):
            self.nwc_forecast.update({year:netCDF4.Dataset(path_netCDF % year)})
            self.nwc_forecast_up.update({year:netCDF4.Dataset(path_netCDF_up % year)})
            self.nwc_uxt.update({year: self.nwc_forecast[year]['issue_time'][:]}) 
            self.nwc_dates.update({year: [pd.Timestamp(i, unit='s') for i in self.nwc_uxt[year]]})        
    
    def close_netCDF(self):
        for year in range(2019,2023):
            self.nwc_forecast[year].close()
            self.nwc_forecast_up[year].close()
        
    def __init_years_selector__(self):
        self.years_to_select = [{'value':year, 'label':'%d'%year} for year in range(2019,2023)]
        self.years_to_select.append({'value':'All','label':'all'})
    
    def get_info4gauge(self, usgs_id, year, lead):        
        #Get the observed data
        qo = np.load('/mnt/y/flow/USGS_observed/%d/%d_usgs_%s.npz' % (year, year,usgs_id))
        uxt_u = np.unique(qo['data']['uxt'])
        #Computes the shared data
        flow_o = np.ones(self.nwc_uxt[year].size)*-999
        shared1 = np.argwhere(np.in1d(self.nwc_uxt[year], uxt_u)).T[0]
        shared2 = np.argwhere(np.in1d(uxt_u, self.nwc_uxt[year])).T[0]
        flow_o[shared1] = qo['data']['val'][shared2]*0.028
        flow_o[flow_o <= 0] = np.nan
        flow_p = np.copy(flow_o)
        flow_o = np.roll(flow_o,lead)
        self.flow_o = flow_o
        self.flow_p = flow_p
        #Reads the NWC assimilated and upstream
        xi = np.where(self.nwc_forecast[year]['usgs_id'][:] == usgs_id)[0][0]        
        flow_s = self.nwc_forecast[year]['flow'][xi,lead-1,:]/100
        flow_s[flow_s <= 0] = np.nan
        self.flow_nwc_a = flow_s
        #Reads the data from upsegment
        xi = np.where(self.nwc_forecast_up[year]['usgs_id'][:] == usgs_id)[0][0]        
        flow_u = self.nwc_forecast_up[year]['flow'][xi,lead-1,:]/100
        flow_u[flow_u <= 0] = np.nan
        self.flow_nwc_u = flow_u
        #Get the pretty dates 
        self.dates = [pd.Timestamp(i+3600*lead, unit='s') for i in self.nwc_uxt[year]]        
        
    def get_hrrr4gauge(self, usgs_id, year):
        #Get the info for the conditional on the rainfall 
        area = self.hrrr_areas.loc[self.current_usgs, ' area']
        idx_hrr = np.where(self.hrrr_usgs == self.current_usgs)[0][0]
        self.hrrr_rain = self.hrrr_totals[idx_hrr]/(area)        
        
    def compute_rel_error(self):
        #Compute the relative errors        
        self.rel_error_nwc_a = 100*(self.flow_nwc_a-self.flow_o)/self.flow_o
        self.rel_error_nwc_u = 100*(self.flow_nwc_u-self.flow_o)/self.flow_o
        self.rel_error_nwc_p = 100*(self.flow_p-self.flow_o)/self.flow_o
    
    def plot_flow(self, usgs_id, lead, year):        
        self.dates = [pd.Timestamp(i+3600*lead, unit='s') for i in self.nwc_uxt[year]]
        name = 'USGS ID: %s, Area: %.1f km2' % (usgs_id, self.usgs.loc[usgs_id,'area'])
        #Makes the figure
        fig = make_subplots(rows = 2, cols = 1, shared_xaxes = True,
                            vertical_spacing = 0.02,
                            row_heights=[0.7, 0.3])
        #fig = go.Figure()        
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.flow_o, 
                    name = 'Observed', 
                    line=dict(color=plotly_colors[0],width=4.5)),row=1,col=1)
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.flow_nwc_a, 
                    name = 'NWC Assimilated', 
                    line=dict(color = plotly_colors[1], width=3)),row=1,col=1)
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.flow_nwc_u, 
                    name = 'NWC Upstream', 
                    line=dict(color=plotly_colors[2], width=3)),row=1,col=1)
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.flow_p, 
                    name = 'Persistence', 
                    line=dict(color=plotly_colors[3], width=3)),row=1,col=1)
        
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.rel_error_nwc_a, 
                    name = 'NWC Assimilated', 
                    line=dict(color=plotly_colors[1], width=3)),row=2,col=1)
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.rel_error_nwc_u, 
                    name = 'NWC Upstream', 
                    line=dict(color=plotly_colors[2], width=3)),row=2,col=1)
        fig.add_trace(
            go.Scatter(x=self.dates, 
                    y=self.rel_error_nwc_p, 
                    name = 'Persistence', 
                    line=dict(color=plotly_colors[3], width=3)),row=2,col=1)        
        
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Streamflow [cms]",            
        )
        return fig, name
        
    def plot_rel_error_histogram(self, bmin, bmax, bsize, percentile, hrrr):
                        
        #GGenerate the bins
        bins = np.arange(bmin,bmax,bsize)
        qmin = np.percentile(self.flow_o[self.flow_o > 0],percentile)
        rmin = np.where(self.hrrr_rain > hrrr)[0]
        pos = np.where((self.flow_o[rmin] > qmin) | (self.flow_nwc_u[rmin] > qmin) | (self.flow_p[rmin] > qmin))[0]

        #Get the histograms 
        _a = self.rel_error_nwc_a.data[pos]
        ha,b = np.histogram(_a[_a > -999], bins = bins)
        ha = 100*(ha.astype(float) / ha.sum())
        _a = self.rel_error_nwc_u.data[pos]
        hu,b = np.histogram(_a[_a > -999], bins = bins)
        hu = 100*(hu.astype(float) / hu.sum())
        _a = self.rel_error_nwc_p[pos]
        hp,b = np.histogram(_a[_a > -999], bins = bins)
        hp = 100*(hp.astype(float) / hp.sum())

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        fig.add_trace(
            go.Scatter(x=b, y=ha, name = 'NWC Assimilated', 
                    line=dict(color=plotly_colors[1],width=4.5)
            )    
        )

        fig.add_trace(
            go.Scatter(x=b, y=hu, name = 'NWC Upstream', 
                    line=dict(color=plotly_colors[2],width=4.5)
            )    
        )

        fig.add_trace(
            go.Scatter(x=b, y=hp, name = 'Persistence', 
                    line=dict(color=plotly_colors[3],width=4.5)
            )    
        )

        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "PDF [%]",            
            xaxis_title = "Relative error",            
        )
        return fig, pos.shape[0]
    
    def plot_rel_histogram_region(self, reg, lead, met, bmin, bmax, bsize):
        bins = np.linspace(bmin,bmax,bsize)
        u_reg = self.usgs.loc[self.usgs.OBJECTID == reg]
        idx_reg = {}
        for k in self.met_mu_error.keys():
            idx_reg.update({k: u_reg.index.intersection(self.met_mu_error[k]['mean'].index)})        

        fig = go.Figure()
        for c, k in enumerate(['nwc','up','per']):
            _a = np.copy(self.met_mu_error[k]['mean']['%s_%d' % (met, lead)])
            _b = np.copy(self.met_mu_error[k]['mean'].loc[idx_reg[k], '%s_%d' % (met, lead)])
            _a[_a == 0] = ma.masked
            h, b = np.histogram(_a, bins = bins)
            h = h.astype(float) / h.sum()

            _b[_b == 0] = ma.masked
            hr, br = np.histogram(_b, bins = bins)
            hr = hr.astype(float) / hr.sum()
            
            fig.add_trace(
                go.Scatter(x = b, y = h, name = k,opacity = 0.3,
                        line=dict(color=plotly_colors[c+1],width=4.5), showlegend = False)
            )

            fig.add_trace(
                go.Scatter(x = br, y = hr, name = '%s for region %d' % (k, reg),
                        line=dict(color=plotly_colors[c+1],width=4.5))
            )
        
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "PDF",
            xaxis_title = "Relative error",
        )
            
        return fig
    
    def plot_rel_error_scatter(self, reg, lead, met):
        u_reg = self.usgs.loc[self.usgs.OBJECTID == reg]
        idxper = u_reg.index.intersection(self.met_mu_error['per']['mean'].index)
        idxnwc = u_reg.index.intersection(self.met_mu_error['nwc']['mean'].index)
        idxup = u_reg.index.intersection(self.met_mu_error['up']['mean'].index)

        fig = go.Figure(
            go.Scatter(mode="markers",
                x = u_reg.loc[idxper, 'area'], y = self.met_mu_error['per']['mean'].loc[idxper, '%s_%d' % (met, lead)],
                name = 'Persistence',
                marker=dict(size=12, 
                            color = plotly_colors[3],
                            line=dict(width=0.5,
                                    color='black'))
            )
        )

        fig.add_trace(
            go.Scatter(mode="markers",
                x = u_reg.loc[idxnwc, 'area'], y = self.met_mu_error['nwc']['mean'].loc[idxnwc, '%s_%d' % (met, lead)],
                name = 'NWC Assimilated',
            marker=dict(size=12, 
                    color = plotly_colors[1],
                    line=dict(width=0.5,
                            color='black'))
            )
        )

        fig.add_trace(
            go.Scatter(mode="markers",
                x = u_reg.loc[idxup, 'area'], y = self.met_mu_error['up']['mean'].loc[idxup, '%s_%d' % (met, lead)],
                name = 'NWC Upstream',
            marker=dict(size=12, 
                    color = plotly_colors[2],
                    line=dict(width=0.5,
                            color='black'))
            )
        )

        fig.update_xaxes(type="log",)# range=[0,5]) 
        fig.update_yaxes(type="log",)

        fig.update_layout(
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01),
                    showlegend = True,
                    margin=dict(t=0, b=0, l=0, r=0),
                    yaxis_title = "Relative error",
                    xaxis_title = "Upstream Area [Km2]",
                )
        return fig
    
    def plot_map(self):                
        #Adds the projects in the region        
        t = ['%s, id:%d' % (i,j) for i,j in zip(self.rlf_df.RFC_NAME, self.rlf_df.OBJECTID)]
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson = self.rlf_geojson,
                colorscale="RdBu",
                locations=self.rlf_df.OBJECTID, 
                featureidkey="properties.OBJECTID",
                z = self.rlf_df.OBJECTID,
                zmin = 2, zmax = 13,
                marker_opacity = 0.3,
                marker_line_width = 0,
                text = t,
                hoverinfo = 'text'
                )
        )
        fig.update_traces(showscale=False)
        #USGS gages
        t = ['%s, Area: %.1f km2' % (i, self.usgs.loc[i,'area']) for i in self.usgs.index]
        fig.add_trace(go.Scattermapbox(
                mode = 'markers',
                lon = self.usgs.lon,
                lat = self.usgs.lat,
                marker=go.scattermapbox.Marker(
                    size=16,
                    color='black',                    
                ),                                
            ))        
        fig.add_trace(go.Scattermapbox(
                mode = 'markers',
                lon = self.usgs.lon,
                lat = self.usgs.lat,                
                marker=go.scattermapbox.Marker(
                    size=13,
                    color=plotly_colors[2],
                    opacity = 0.8,  
                    allowoverlap = False                  
                ),                               
                text=t,  
                hoverinfo = 'text'
            ))
        
        #Beauty layout
        fig.update_layout(
            hovermode='closest',
            showlegend=False,
            margin ={'l':0,'t':0,'b':0,'r':0},
            mapbox=dict(                    
                bearing=0,
                center=dict(                    
                    lat=38,
                    lon=-97
                ),
                pitch=0,
                zoom=3.4,
                style = "open-street-map"                                  
            )
        )
        
        return fig