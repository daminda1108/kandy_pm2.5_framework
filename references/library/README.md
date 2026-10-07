# Reference library

Built by `references/build_library.py` from the thesis/preprint bibliography (`kandy_pm25/docs/paper/references.bib`) and the Paper 1 bibliography (`papers/paper1_information_budget/references/references.bib`), merged by DOI. Re-run the script after adding references; existing PDFs are kept.

- **122 unique works**; **41 PDFs held** as `<citekey>.pdf`; **53 to fetch through the university library** (closed access or no PDF link); **28 without a DOI** (books, reports, datasets, web pages).
- Only legal open-access copies were downloaded (OpenAlex locations: publisher, arXiv, repositories).
- `INDEX.csv`: key, year, authors, title, venue, DOI, which document cites it, PDF file, status.
- `library.bib`: both bibliographies merged, with `file = {<citekey>.pdf}` for Zotero (File > Import, then point the linked-file base directory at this folder).
- The original downloads in `references/papers/` are left as they were; matched ones are copied here.

## Other papers in references/papers/ (not cited in either bibliography, or no DOI on their first pages)

- `1-s2.0-S0012825225002375-main.pdf`
- `1-s2.0-S0021999118307125-am.pdf`
- `1-s2.0-S0048969725022338-main.pdf`
- `1-s2.0-S016041202500666X-main.pdf`
- `1-s2.0-S0301479725036527-main.pdf`
- `1-s2.0-S1364815224003736-main.pdf`
- `1-s2.0-S2215016125004418-main.pdf`
- `162-1-1080-1-10-20090108.pdf`
- `2402.03784v2.pdf`
- `2503.18849v1 (1).pdf`
- `66270f118263b.pdf`
- `airpollutionKandyVilani.pdf`
- `ijsrp.pdf`
- `NeurIPS-2024-pinnacle-a-comprehensive-benchmark-of-physics-informed-neural-networks-for-solving-pdes-Paper-Datasets_and_Benchmarks_Track.pdf`
- `PAHpaper2011.pdf`
- `particulate-pollution-spm-pm10-pm2-5-ratio-colombo-atmosphere.pdf`
- `S0012825225002375.htm`

## To fetch through the university library

| key | year | title | DOI |
|---|---|---|---|
| Basagana2012 | 2012 | Effect of the number of measurement sites on land use regression models in estimating loca | 10.1016/j.atmosenv.2012.01.064 |
| Bauer2015 | 2015 | The quiet revolution of numerical weather prediction | 10.1038/nature14956 |
| CAMSforecast | 2024 | CAMS global atmospheric composition forecasts | 10.24381/04a0b097 |
| ChenLin2022 | 2022 | Exposure assessment of PM2.5 using smart spatial interpolation on regulatory air quality s | 10.1016/j.envpol.2021.118401 |
| Choi2026 | 2026 | Optimal sensor placement in low-cost PM2.5 sensor networks using value of information and  | 10.1088/1748-9326/ae2b89 |
| Cimorelli2005 | 2005 | AERMOD: A Dispersion Model for Industrial Source Applications. Part I: General Model Formu | 10.1175/jam2227.1 |
| CopernicusDEM | 2021 | Copernicus Global Digital Elevation Model (GLO-30) | 10.5270/esa-c5d3d65 |
| Davison1997 | 1997 | Bootstrap Methods and their Application | 10.1017/cbo9780511802843 |
| Dharmapriya2024 | 2024 | Atmospheric quality through analysis of dry and wet deposition at selected locations in Ka | 10.1007/s11869-023-01431-z |
| Di2019 | 2019 | An ensemble-based model of PM2.5 concentration across the contiguous United States with hi | 10.1016/j.envint.2019.104909 |
| Didan2021 | 2021 | MODIS/Terra Vegetation Indices 16-Day L3 Global 1km SIN Grid V061 | 10.5067/modis/mod13a2.061 |
| Eskridge1997 | 1997 | Separating different scales of motion in time series of meteorological variables | 10.1175/1520-0477(1997)078 |
| Farr2007 | 2007 | The Shuttle Radar Topography Mission | 10.1029/2005rg000183 |
| Field2007 | 2007 | Bootstrapping clustered data | 10.1111/j.1467-9868.2007.00593.x |
| FIRMS_MCD14DL | 2016 | MODIS Collection 6 NRT Hotspot / Active Fire Detections MCD14DL | 10.5067/firms/modis/mcd14dl.nrt.006 |
| Forthofer2014 | 2014 | A comparison of three approaches for simulating fine-scale surface winds in support of wil | 10.1071/wf12089 |
| Gassmann2000 | 2000 | Air Pollution Potential: Regional Study in Argentina | 10.1007/s002679910029 |
| Giglio2016 | 2016 | The collection 6 MODIS active fire detection algorithm and fire products | 10.1016/j.rse.2016.02.054 |
| Gorelick2017 | 2017 | Google Earth Engine: Planetary-scale geospatial analysis for everyone | 10.1016/j.rse.2017.06.031 |
| Gressent2020 | 2020 | Data fusion for air quality mapping using low-cost sensor observations: Feasibility and ad | 10.1016/j.envint.2020.105965 |
| Hansen2013 | 2013 | High-Resolution Global Maps of 21st-Century Forest Cover Change | 10.1126/science.1244693 |
| Hersbach2020 | 2020 | The ERA5 global reanalysis | 10.1002/qj.3803 |
| Hoek2008 | 2008 | A review of land-use regression models to assess spatial variation of outdoor air pollutio | 10.1016/j.atmosenv.2008.05.057 |
| Hopke2016 | 2016 | Review of receptor modeling methods for source apportionment | 10.1080/10962247.2016.1140693 |
| Howard1966 | 1966 | Information Value Theory | 10.1109/tssc.1966.300074 |
| Huffman2020 | 2020 | Integrated Multi-satellite Retrievals for the Global Precipitation Measurement (GPM) Missi | 10.1007/978-3-030-24568-9_19 |
| Just2020 | 2020 | Advancing methodologies for applying machine learning and evaluating spatiotemporal models | 10.1016/j.atmosenv.2020.117649 |
| Kanaroglou2005 | 2005 | Establishing an air pollution monitoring network for intra-urban population exposure asses | 10.1016/j.atmosenv.2004.06.049 |
| Keller2021 | 2021 | Description of the NASA GEOS Composition Forecast Modeling System GEOS-CF v1.0 | 10.1029/2020ms002413 |
| Lakens2017 | 2017 | Equivalence tests: A practical primer for t tests, correlations, and meta-analyses | 10.1177/1948550617697177 |
| Lakens2018 | 2018 | Equivalence testing for psychological research: A tutorial | 10.1177/2515245918770963 |
| Lenschow2001 | 2001 | Some ideas about the sources of PM10 | 10.1016/s1352-2310(01)00122-4 |
| Mampitiya2023 | 2023 | Machine Learning Techniques to Predict the Air Quality Using Meteorological Data in Two Ur | 10.3390/environments10080141 |
| Martin2019 | 2019 | No one knows which city has the highest concentration of fine particulate matter | 10.1016/j.aeaoa.2019.100040 |
| Pekel2016 | 2016 | High-resolution mapping of global surface water and its long-term changes | 10.1038/nature20584 |
| Pesaresi2023 | 2023 | GHS-BUILT-V R2023A - GHS built-up volume grids derived from joint assessment of Sentinel2, | 10.2905/ab2f107a-03cd-47a3-85e5-139d8ec63283 |
| Rao1994 | 1994 | Detecting and tracking changes in ozone air quality | 10.1080/10473289.1994.10467303 |
| Reid2015 | 2015 | Spatiotemporal prediction of fine particulate matter during the 2008 Northern California w | 10.1021/es505846r |
| Ryan2016 | 2016 | A Review of Modern Computational Algorithms for Bayesian Optimal Design | 10.1111/insr.12107 |
| Samrat2025 | 2025 | Observation impact evaluation through data denial experiments in the Met Office global num | 10.1002/qj.5002 |
| Schiavina2023 | 2023 | GHS-POP R2023A - GHS population grid multitemporal (1975-2030) | 10.2905/2ff68a52-5b5b-4a22-8f40-c41da8332cfe |
| SchiavinaSMOD2023 | 2023 | GHS-SMOD R2023A - GHS settlement layers, application of the Degree of Urbanisation methodo | 10.2905/jrc.spx1fdr |
| Schneider2017 | 2017 | Mapping urban air quality in near real-time using observations from low-cost sensors and m | 10.1016/j.envint.2017.05.005 |
| Senarathna2026 | 2026 | Enhancing low-cost PM2.5 air quality monitoring sensors through sensor calibration using r | 10.1007/s10661-026-15623-4 |
| Simpson1951 | 1951 | The Interpretation of Interaction in Contingency Tables | 10.1111/j.2517-6161.1951.tb00088.x |
| Stull1988 | 1988 | An Introduction to Boundary Layer Meteorology | 10.1007/978-94-009-3027-8 |
| Swanson2026 | 2026 | Winter inversions and summer smoke: A season-dependent approach to PM2.5 modeling with low | 10.1016/j.scitotenv.2026.181915 |
| Veefkind2012 | 2012 | TROPOMI on the ESA Sentinel-5 Precursor: a GMES mission for global observations of the atm | 10.1016/j.rse.2011.09.027 |
| Verghese2022 | 2022 | Optimal design of air quality monitoring networks: A systematic review | 10.1007/s00477-022-02187-1 |
| Wang2012LUR | 2012 | Systematic evaluation of land use regression models for NO2 | 10.1021/es204183v |
| Wickramasinghe2011 | 2011 | PM10-bound polycyclic aromatic hydrocarbons: Concentrations, source characterization and e | 10.1016/j.atmosenv.2011.02.032 |
| Zanaga2022 | 2022 | ESA WorldCover 10 m 2021 v200 | 10.5281/zenodo.7254221 |
| Zhang2025 | 2025 | Low-Cost Particulate Matter Mass Sensors: Review of the Status, Challenges, and Opportunit | 10.1021/acssensors.4c03293 |

## Without a DOI

| key | year | title | venue |
|---|---|---|---|
| Angelopoulos2023 | 2023 | Conformal Prediction: A Gentle Introduction | Foundations and Trends in Machine Learning |
| Bruinsma2021 | 2021 | The Gaussian Neural Process |  |
| CFR50N |  | Appendix N to Part 50 -- Interpretation of the National Ambient Air Quality Standards for  |  |
| CFR58E | 2024 | Probe and Monitoring Path Siting Criteria for Ambient Air Quality Monitoring |  |
| CNEMC | 2026 | Real-time air quality data, archived by He Qin |  |
| DCS2012Census | 2012 | Census of Population and Housing 2012 |  |
| Dehideniya2018 | 2018 | Optimal Bayesian design for discriminating between models with intractable likelihoods in  | Computational Statistics \& Data Analysis |
| Duvall2021 | 2021 | Performance Testing Protocols, Metrics, and Target Values for Fine Particulate Matter Air  |  |
| Elangasinghe2008 | 2008 | Determination of atmospheric PM10 concentration in Kandy in relation to traffic intensity | Journal of the National Science Foundation of Sri  |
| Gordon2020 | 2020 | Convolutional Conditional Neural Processes | International Conference on Learning Representatio |
| Huffman2023 | 2023 | Algorithm Theoretical Basis Document (ATBD) Version 07 for the NASA Global Precipitation M |  |
| Jayalath2023 | 2023 | Assessment of Transboundary Pollution from Colombo to Kandy on the Atmospheric Deposition  | Sri Lankan Journal of Applied Sciences |
| Ke2017 | 2017 | LightGBM: A Highly Efficient Gradient Boosting Decision Tree | Advances in Neural Information Processing Systems  |
| NaturalEarth | 2026 | Natural Earth: free vector and raster map data |  |
| Nguyen2022 | 2022 | Transformer Neural Processes: Uncertainty-Aware Meta Learning via Sequence Modeling | International Conference on Machine Learning ({ICM |
| Ntziachristos2000 | 2000 | COPERT III Computer programme to calculate emissions from road transport: Methodology and  |  |
| OpenAQ | 2026 | OpenAQ: open air quality data platform |  |
| OpenStreetMap | 2026 | OpenStreetMap |  |
| Pedregosa2011 | 2011 | Scikit-learn: Machine Learning in Python | Journal of Machine Learning Research |
| Prokhorenkova2018 | 2018 | CatBoost: unbiased boosting with categorical features | Advances in Neural Information Processing Systems  |
| PurpleAir | 2026 | PurpleAir sensor data |  |
| Romano2019 | 2019 | Conformalized Quantile Regression | Advances in Neural Information Processing Systems  |
| Senarathna2024 | 2024 | PM2.5 air pollution trends and patterns in Kandy, Sri Lanka | Ceylon Journal of Science |
| Sprenger2021 | 2021 | Simpson's Paradox | The Stanford Encyclopedia of Philosophy (Summer 20 |
| Vovk2005 | 2005 | Algorithmic Learning in a Random World | Springer |
| Whiteman2000 | 2000 | Mountain Meteorology: Fundamentals and Applications | Oxford University Press |
| WHO2021 | 2021 | WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen di |  |
| WorldBank2020KMTT | 2020 | Project Information Document: Kandy Multimodal Transport Terminal Development Project (P17 |  |
