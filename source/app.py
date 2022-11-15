import dash
from dash import dcc, ctx
import json
#import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
#import dash_html_components as html
from dash import html
from datetime import date
import numpy as np
from misc import misc
#Local packages
import plotly.express as px
import plotly.graph_objects as go
import base64

###########################################################################################################################################################################
# Initialize variables 

#Initializae the misc element that control figures 
usgs_id = '01030500'
year = 2019
region = 2
mi = misc(year, usgs_id, region)
fig_map = mi.plot_map()
#mi.get_flow4gauge(usgs_id, year)
mi.get_info4gauge(usgs_id, year, 1)
mi.get_hrrr4gauge(usgs_id, year)
mi.compute_rel_error()
fig_flow, name_flow = mi.plot_flow(usgs_id,1,year)
fig_rel_hist, hist_nrecords = mi.plot_rel_error_histogram(-50,200,20,50,0)
fig_reg_scatter = mi.plot_rel_error_scatter(region, 1, 'ame')
fig_reg_histogram = mi.plot_rel_histogram_region(region, 1, 'ame', -50, 200, 15)                        

###########################################################################################################################################################################
# Define the server 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

###########################################################################################################################################################################
#Tabs content

control_card = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                #Year dropdown 
                html.Div(
                    [
                        dbc.Label("Year to analyze"),
                        dcc.Dropdown(
                            id = 'plot-flow-year-selector',
                            options = mi.years_to_select,
                            value = mi.years_to_select[0]['value'],
                            multi = False,
                            style={
                                'width':'140px'
                            }
                        ),
                    ]
                ),    
            ],md = 2),
            dbc.Col([
                html.Div([
                    dbc.Label('Lead time [hours]'),
                    #Lead time dropdo
                    dcc.Slider(
                        id = 'plot-flow-lead-time-sel',
                        min = 1,
                        max = 18,
                        step = 1,
                        value = 1,                
                    )  
                ])  
            ], md = 7),
            dbc.Col([
                html.Div([
                    dbc.Label('P(HRRR>R) [mm]'),
                    #Lead time dropdo
                    dcc.Slider(0,4,1,value=0,
                    id='hrrr-condition',
                    tooltip={"placement": "bottom", "always_visible": True}                    
                ), 
                ])  
            ], md = 3)            
        ])
    ])
)

tab1_content = dbc.Card(
    dbc.CardBody(
        [                        
            dbc.Label(name_flow, id = 'name-flow'),
            dcc.Graph(
                id = 'plot-flow',
                figure = fig_flow,
                style = {'width': '85vh', 'height': '40vh'},            
            ),                                                            
        ]
    ),color="secondary", outline=True
)

hist_control_card = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Min bin value"),
                dcc.Slider(-200,200,10,value=0,
                    id='bmin',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        -200:{'label':'-200'},
                        0:{'label':'0'},
                        200:{'label':'200'}
                    },
                ),    
            ]
        ),
        html.Div(
            [
                dbc.Label("Max bin value"),
                dcc.Slider(50,500,10,value=100,
                    id='bmax',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        50:{'label':'50'},
                        200:{'label':'200'},
                        400:{'label':'400'}
                    },
                ),    
            ]
        ),
        html.Div(
            [
                dbc.Label("Histogram Interval size"),
                 dcc.Slider(5,30,1,value=15,
                    id='bsize',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        5:{'label':'0'},
                        15:{'label':'15'},
                        30:{'label':'30'}
                    },
                ),           
            ]
        ),
        html.Div(
            [
                dbc.Label("P(Q>Qp)"),
                dcc.Slider(0,99,1,value=0,
                    id='q-condition',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        0:{'label':'0'},
                        50:{'label':'50'},
                        100:{'label':'100'}
                    },
                ),                
            ]
        ),
        html.Div(
            [
                dbc.Label("P(HRRR>R)"),
                dcc.Slider(0,8,1,value=0,
                    id='hrrr-condition-gauge',
                    tooltip={"placement": "bottom", "always_visible": True}                    
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label('Total records: '),
                dbc.Label(hist_nrecords, id = 'total-hist-records'),                
            ]
        ),        
        
    ]
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
        dbc.Row([
            dbc.Col([
                dbc.Label(name_flow, id = 'name-flow-rel-error'),
                dcc.Graph(
                    id = 'plot-rel-hist',
                    figure = fig_rel_hist,
                    style = {'width': '60vh', 'height': '40vh'},            
                ),                                                                                    
            ], md = 8),
            dbc.Col(hist_control_card, md = 4)
        ])          
        ]
    ),color="secondary", outline=True
)

rel_err_scatter_control_card = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Absolute?"),
                dcc.Dropdown(
                    id='rel_err_scatter_abs',
                    options = [
                        {'value':'ame','label':'True'},
                        {'value':'me','label':'False'},
                    ],
                    value = 'ame'                    
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Statistic"),
                dcc.Dropdown(
                    id='rel_err_scatter_statistic',
                    options = [
                        {'value':'mean','label':'Mean'}
                    ],
                    value='mean'
                ),
            ]
        ),           
    ]
)

tab3_content = dbc.Card(
    dbc.CardBody(
        [
        dbc.Row([
            dbc.Col([
                dbc.Label('Mean error by region'),
                dcc.Graph(
                    id = 'scatter-rel-error-region',
                    figure = fig_reg_scatter,
                    style = {'width': '70vh', 'height': '40vh'},            
                ),                                                                                    
            ], md = 9),
            dbc.Col(rel_err_scatter_control_card, md = 3)
        ])          
        ]
    ),color="secondary", outline=True
)

rel_err_histogram_control_card = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Absolute?"),
                dcc.Dropdown(
                    id='rel_err_histogram_abs',
                    options = [
                        {'value':'ame','label':'True'},
                        {'value':'me','label':'False'},
                    ],
                    value = 'ame'                    
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Statistic"),
                dcc.Dropdown(
                    id='rel_err_histogram_statistic',
                    options = [
                        {'value':'mean','label':'Mean'}
                    ],
                    value='mean'
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Min bin value"),
                dcc.Slider(-200,200,10,value=0,
                    id='bmin_reg',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        -200:{'label':'-200'},
                        0:{'label':'0'},
                        200:{'label':'200'}
                    },
                ),    
            ]
        ),
        html.Div(
            [
                dbc.Label("Max bin value"),
                dcc.Slider(50,500,10,value=100,
                    id='bmax_reg',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        50:{'label':'50'},
                        200:{'label':'200'},
                        400:{'label':'400'}
                    },
                ),    
            ]
        ),
        html.Div(
            [
                dbc.Label("Histogram Interval size"),
                 dcc.Slider(5,30,1,value=15,
                    id='bsize_reg',
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={
                        5:{'label':'0'},
                        15:{'label':'15'},
                        30:{'label':'30'}
                    },
                ),           
            ]
        ),       
        # html.Div(
        #     [
        #         dbc.Label("P(HRRR>R)"),
        #         dcc.Slider(0,4,1,value=0,
        #             id='hrrr-condition-reg',
        #             tooltip={"placement": "bottom", "always_visible": True}                    
        #         ),
        #     ]
        # ),
        html.Div(
            [
                dbc.Label('Total records: '),
                dbc.Label(hist_nrecords, id = 'total-hist-records-reg'),                
            ]
        ),        
        
    ]
)

tab4_content = dbc.Card(
    dbc.CardBody(
        [
        dbc.Row([
            dbc.Col([
                dbc.Label('Histogram'),
                dcc.Graph(
                    id = 'histogram-rel-error-region',
                    figure = fig_reg_histogram,
                    style = {'width': '70vh', 'height': '40vh'},            
                ),                                                                                    
            ], md = 9),
            dbc.Col(rel_err_histogram_control_card, md = 3)
        ])          
        ]
    ),color="secondary", outline=True
)

###########################################################################################################################################################################
#Web page layout 
app.layout = dbc.Container([
    html.H1("NWC error evaluation platform"),    
    html.Hr(),
    dbc.Row([
        #Left Column, has the map and will have overal figures 
        dbc.Col([                        
            
            dcc.Graph(
                id = 'plot-map',
                clickData = {'points': [{'text': '%s,0' % usgs_id}]},
                figure = fig_map,
                style={'width': '95vh', 'height': '50vh'},
                config={"toImageButtonOptions": {"scale":4, "filename": 'event_streamflow'}}
            ),
        ], width = 6),
        dbc.Col([                        
            #Tabs presenting results of the selected gauge
            dbc.Tabs([
                dbc.Tab(tab1_content, tab_id = "tab_flow", label="Gauge Flow"),
                dbc.Tab(tab2_content, tab_id = "tab_rel_error", label="Gauge Rel Error"),                
                dbc.Tab(tab3_content, tab_id = "tab_rel_error_scatter", label="Error vs Area"),                
                dbc.Tab(tab4_content, tab_id = "tab_rel_error_histogram", label="Error PDF"),                
            ], active_tab = mi.active_tab, id = "tabs",),
            #Place the controls to handle the plots and metrics
            control_card
                        
        ], width = 6)
    ],align="center"),

    

], fluid = True)

# ###########################################################################################################################################################################
# #Call back functions

#Updates figures based on the clicked gauge
@app.callback(
    Output('plot-flow','figure'),    
    Output('name-flow','children'),
    Output('name-flow-rel-error','children'),
    Input('plot-map','clickData'),
    Input('plot-flow-year-selector','value'),
    Input('plot-flow-lead-time-sel','value'),    
)
def update_figures_from_click(click,year,lead):#,bmin,bmax,bsize,q_condition):
    #print(ctx.triggered[0]['prop_id'])
    usgs_id = click['points'][0]['text'].split(',')[0]    
    if len(click['points'][0]['text'].split(':')[-1]) > 3:                
        if usgs_id != mi.current_usgs:
            mi.current_usgs = usgs_id
            mi.get_hrrr4gauge(usgs_id, year) 
    print(mi.current_usgs)
    #If click on new gauge or year change load the data 
    #trigger = ctx.triggered[0]['prop_id']
    #if trigger == 'plot-map.clickData' or trigger == 'plot-flow-year-selector.value':
    mi.get_info4gauge(mi.current_usgs, year, lead)
    #Update the errors baseed on the lead value
    #if trigger == 'plot-flow-lead-time-sel.value':        
    mi.compute_rel_error()        
    #Update the figures    
    #if trigger == 'bmin.value' or trigger == 'bmax.value' or trigger == 'bsize.value' or trigger == 'q-condition.value':
    fig_flow, name_flow = mi.plot_flow(mi.current_usgs, lead, year)    
    #return the values
    return fig_flow, name_flow, name_flow

@app.callback(    
    Output('plot-rel-hist','figure'),
    Output('total-hist-records', 'children'),
    Input('bmin','value'),
    Input('bmax','value'),
    Input('bsize','value'),
    Input('q-condition','value'),
    Input('hrrr-condition-gauge','value')
)
def updte_rel_error_histogram(bmin,bmax,bsize,q_condition,hrrmin):
    fig, nrecords = mi.plot_rel_error_histogram(bmin, bmax, bsize, q_condition, hrrmin)        
    return fig, nrecords


@app.callback(    
    Output('scatter-rel-error-region','figure'),
    Input('rel_err_scatter_abs','value'),
    Input('rel_err_scatter_statistic','value'),
    Input('plot-map','clickData'),
    Input('plot-flow-lead-time-sel','value'),
    Input('hrrr-condition','value')        
)
def update_rel_error_scatter(abs,met,region,lead,condition):
    if condition != mi.current_condition:
        mi.load_error_metrics(condition)
    if len(region['points'][0]['text'].split(':')[-1]) < 3:
        mi.current_region = int(region['points'][0]['text'].split(':')[-1])    
    fig = mi.plot_rel_error_scatter(mi.current_region, lead, abs)
    return fig

@app.callback(    
    Output('histogram-rel-error-region','figure'),
    Input('rel_err_histogram_abs','value'),
    Input('rel_err_histogram_statistic','value'),
    Input('plot-map','clickData'),
    Input('plot-flow-lead-time-sel','value'),  
    Input('bmin_reg','value'),
    Input('bmax_reg','value'),
    Input('bsize_reg','value'),          
    Input('hrrr-condition','value')
)
def update_rel_error_histogram(abs,met,region,lead,bmin,bmax,bsize, condition):
    #Checks if there is a change of region
    if len(region['points'][0]['text'].split(':')[-1]) < 3:
        mi.current_region = int(region['points'][0]['text'].split(':')[-1])    
    #Checks if the hrrr condition has changed
    if condition != mi.current_condition:
        mi.load_error_metrics(condition)    
    #Updates the figure
    fig = mi.plot_rel_histogram_region(mi.current_region, lead, abs, bmin, bmax, bsize)    
    return fig

###########################################################################################################################################################################
#Excecution

if __name__ == '__main__':
    app.run_server(debug=True, port = 8889,)
