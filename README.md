# nwc_evaluation_platform
nwc_evaluation_platform

## Time series data structure:

- YYYY_nwc_error.nc (done): Contains the hourly relative errors for the gauges:
    - er_nwc: NWC with data assimilation
    - er_per: Temporal persistence
- YYYY_nwc_upsegment.nc (done): Contains the hourly relative errors for the gauges:
    - er_nwc: NWC with data assimilation but upstream of the gauge (less data asiimilation)
    - er_per: Temporal persistence, same as above but only at gauges with upsegment data
- YYYY_spatial_persistence.nc (done): Qp = Qc1 + Qc2 + ... + QcN (usgs_actual_parents_YYYY.csv)
    - per_simple: flow estimated with persistence simple
    - per_scaled: flow estimated with persistence scaled as E(Qo) * (Qp/E(Qp))
    - er_child: Rel error using the spatial persistence simple
    - er_child_sca: Rel error using the spatial persistence scaled

Note: missing the All in every case.

## Summary Metrics data structure:

- YYYY_type_mean_rel_error_condition.gz: Has the mean (me_i) and absmean (ame_i) of the rel error.
    - type: 
        - nwc: NWC with data assimilation (2022 missing)
        - nwcup: NWC without data assimilation (2022 missing)
        - per: termporal persistence (2022 missing)
        - spper: spatial persistence simple (not done yet)
        - spsca: spatial persistence scaled (not done yet)
    - condition:
        - uncond: unconditional
        - hrrr_i: for hrrr total values above i

## Progress

- 