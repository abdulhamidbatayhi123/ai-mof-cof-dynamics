# Literature: MOF/COF water harvesters, device models / digital twins, ML for adsorption processes, water-isotherm data

Compiled 2026-09-25 by a literature-research agent. Rule 8: a source counts only if FETCHED (abstract,
Crossref/OpenAlex record or full text actually opened). SEEN-ONLY entries are leads, not evidence.
Authors are written exactly as the fetched record shows them (initials kept as initials).
"Crossref record" means only metadata (title/authors/year/journal) was confirmed, not content, unless an
abstract is stated.

Status: COMPLETE for this pass (62 source entries S01-S62; synthesis sections after the source log).
Fetch routes used: Crossref API, OpenAlex API, Europe PMC REST (full text where OA), Semantic Scholar API, arXiv API,
Zenodo API, GitHub API, NIST ISODB API, publisher pages via curl. ACS, ScienceDirect, cell.com and nature.com (some)
returned 403/login to automated fetches, so several entries are "metadata only" and say so.

## Source log (appended as fetched)

### S01. Nobel Prize in Chemistry 2025 (Q6) - FETCHED
- URL opened: https://www.nobelprize.org/prizes/chemistry/2025/press-release/ (fetched with curl; the /summary/ page returned HTTP 403 to WebFetch).
- Press release dated 8 October 2025: the Royal Swedish Academy of Sciences awarded the 2025 chemistry prize to
  Susumu Kitagawa (Kyoto University), Richard Robson (University of Melbourne), Omar M. Yaghi (UC Berkeley),
  "for the development of metal-organic frameworks". The release itself names harvesting water from desert air
  as one application.
- Verdict: VERIFIED. Safe to cite as field context (cite the press release URL).

### S02. Kim et al. 2017, Science - MOF-801 solar harvester (Q1) - FETCHED (Crossref record + abstract)
- DOI opened: https://api.crossref.org/works/10.1126/science.aam8743
- Authors (as shown): Hyunho Kim, Sungwoo Yang, Sameer R. Rao, Shankar Narayanan, Eugene A. Kapustin, Hiroyasu Furukawa, Ari S. Umans, Omar M. Yaghi, Evelyn N. Wang. Year 2017. Science.
- Content (abstract): MOF-801 [zirconium fumarate] device driven by natural sunlight; steep uptake over a narrow RH window;
  abstract states 2.8 L water per kg MOF per day at 20% RH. Two Technical Comments in Science (S53 Meunier; S54 Bui,
  Chua, Gordon) dispute the deliverable amount and the efficiency - do not cite 2.8 L/kg/day as measured performance.
- Data form: not verified from this record. SI contents not opened.

### S03. Fathieh et al. 2018, Sci. Adv. - MOF-801 / MOF-303 desert harvester (Q1) - FETCHED (full text via Europe PMC PMC5993474)
- DOI: 10.1126/sciadv.aat3198. Opened: Crossref record, OpenAlex abstract, Europe PMC fullTextXML.
- Authors (Crossref): Farhad Fathieh, Markus J. Kalmutzki, Eugene A. Kapustin, Peter J. Waller, Jingjing Yang, Omar M. Yaghi. 2018.
- Says: prototype with up to 1.2 kg MOF-801 tested in lab and in the Arizona desert; about 100 g water per kg MOF-801 per
  day-night cycle with natural cooling and sunlight only; MOF-303 reported to deliver more than twice that. One cycle per day.
  Uses an energy/air-requirement analysis (q_H,min, q_C,min criteria) rather than a dynamic model.
- Data form: SI has sections "Data acquisition and sensors", "WHC under laboratory conditions", "Harvesting experiments at
  Scottsdale, AZ" plus isotherms at several temperatures (fig. S6) and characteristic curves (fig. S7). Data statement (verbatim
  gist): all data are in paper/Supplementary Materials; "Additional data ... may be requested from the authors". No repository.
- Ground-truth value: device time series (T, RH, uptake) exist only as SI figures -> digitisation needed; 1 cycle/day, 2 materials.

### S04. Hanikel et al. 2019, ACS Cent. Sci. - rapid-cycling MOF-303 harvester (Q1, Q4) - FETCHED (full text via Europe PMC PMC6813556)
- DOI: 10.1021/acscentsci.9b00745 (ACS page returned 403; Europe PMC full text opened).
- Authors (Crossref): Nikita Hanikel, Mathieu S. Prévot, Farhad Fathieh, Eugene A. Kapustin, Hao Lyu, Haoze Wang, Nicolas J. Diercks, T. Grant Glover, Omar M. Yaghi. 2019.
- Says: MOF-303 completes an adsorption-desorption cycle within minutes under mild temperature swing; device made
  1.3 L/kg MOF/day indoors (32% RH, 27 C) and 0.7 L/kg/day in the Mojave (down to 10% RH). 579 g MOF-303 in the exchanger.
- KEY for our project: a controlled CROSS-MATERIAL kinetic comparison - MOF-303, Al-fumarate (Basolite A520), SAPO-34,
  zeolite 13X, all processed as 3 mm packed layers, packing porosity 0.7, grain size 2-5 um; TGA uptake vs time at 30 C and
  20/30/40% RH, desorption at 65/85/120 C and 0% RH; isotherms at 30 C (Fig. 2); duplicate runs (S4.3).
  Adsorption curves described as "apparent monoexponential" (i.e. LDF-like), fitted with R^2 > 99%; initial rate R0,norm
  tabulated (Table 1). Desorption NOT fitted (oven ramp interferes). At 20% RH zeolite 13X is fastest (R0,norm 1.2).
- Data form: figures + Table 1 of normalised rates; SI PDF (dynamic sorption, exchanger details). No deposited dataset found.
- Ground-truth value: HIGH as a small, same-geometry, 4-sorbent uptake-vs-time set for a leave-one-material-out test, but
  must be digitised from figures; desorption curves are confounded by heater dynamics (authors say so).

### S05. Hanikel et al. 2021, Science - multivariate MOF-303 series (Q1, Q4) - FETCHED (Crossref + OpenAlex abstract only)
- DOI: 10.1126/science.abj0890. Authors (Crossref): Nikita Hanikel, Xiaokun Pei, Saumil Chheda, Hao Lyu, WooSeok Jeong, Joachim Sauer, Laura Gagliardi, Omar M. Yaghi. 2021.
- Says: single-crystal XRD + DFT resolve the water filling sequence in MOF-303; multivariate linker mixing tunes binding of
  the first water molecules, giving tunable regeneration temperature/enthalpy and higher productivity without loss of
  capacity/stability.
- Relevance: a family of closely related materials with shifted isotherms - natural "interpolation" test set. Data form not
  verified (full text/SI not opened; Science paywall).

### S06. Nguyen et al. 2020, JACS - COF-432 (Q1, Q5) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/jacs.9b13094. Authors (Crossref): Ha L. Nguyen, Nikita Hanikel, Steven J. Lyle, Chenhui Zhu, Davide M. Proserpio, Omar M. Yaghi. 2020.
- Says: 2D imine-linked COF with voided square grid topology; S-shaped water isotherm with steep step at low RH and no
  hysteresis; regenerable at ultra-low temperature; working capacity retained after 300 adsorption-desorption cycles.
- Relevance: the canonical COF water-harvesting sorbent; paper is a material paper (isotherms + cycling stability), not a
  device demonstration (no L/kg/day device number in the abstract). OA author copy exists (air.unimi.it, per OpenAlex).

### S07. Song, Zheng, Alawadhi, Yaghi 2023, Nature Water - Death Valley passive harvester (Q1) - FETCHED (full-text PDF + Zenodo record)
- DOI: 10.1038/s44221-023-00103-7. Authors (Crossref): Woochul Song, Zhiling Zheng, Ali H. Alawadhi, Omar M. Yaghi. 2023.
  nature.com redirected to login; the article PDF was read from a copy hosted at
  https://bpb-us-e2.wpmucdn.com/sites.wustl.edu/dist/0/4841/files/2025/06/mof-water-harvester.pdf (11 pages, text extracted).
- Says: passive MOF-303 harvester (MOF-303 + 15 wt% graphite pellets, "MOF85-G15"; vacuum-insulated housing; night
  adsorption, sunlight desorption; no power input). 210 g/kg/day (Death Valley) and 285 g/kg/day (Berkeley); Death Valley,
  August 2022: 114-210 g H2O/kg MOF/day with ambient swing 21.9-60.7 C and RH 9.4-36%. One cycle per day.
- Data: "The datasets that support this study are available in Zenodo" - https://doi.org/10.5281/zenodo.7990951.
  Zenodo API record opened: title "Data set (Song et al., Nat. Water)", creators Song, Woochul; Zheng, Zhiling; Alawadhi,
  Ali H.; Yaghi, Omar M.; 2023-07-01; licence CC-BY-4.0; ONE file "Data-Song et al. Nat. Water.opju" (2,315,847 bytes,
  NOT downloaded). .opju is an OriginLab project -> needs Origin (or a converter) to extract the curves.
- Ground-truth value: HIGH - the only Yaghi-group harvester with a deposited, licensed dataset found; likely contains the
  field T/RH/uptake/production traces behind the figures (not verified until opened). Single material (MOF-303 composite).

### S08. Kim et al. 2018, Nat. Commun. - MOF-801 air-cooled device, Tempe AZ (Q1, Q2) - FETCHED (full text via Europe PMC PMC5864962)
- DOI: 10.1038/s41467-018-03162-7. Authors (Europe PMC): Kim H, Rao SR, Kapustin EA, Zhao L, Yang S, Yaghi OM, Wang EN. 2018.
  (OpenAlex lists "Hyunho Kim, Sameer Raghavendra Rao, ..." - use the Europe PMC/Crossref form.)
- Says: ~3 g MOF-801 in a copper-foam layer (packing porosity 0.67, 2.57 mm), 10-40% RH, sub-zero dew points; thermal
  efficiency ~14% with 1.8x optical concentration. SKEPTIC NOTE: the water yield was NOT measured - the paper says accurate
  measurement was not possible with ~3 g and instead used "validated computational predictions" driven by measured ambient/
  condenser temperature, RH and solar flux (predicted ~0.12 L/kg non-concentrated, ~0.28 L/kg/cycle concentrated). Kinetic
  limitation attributed to intra/intercrystalline diffusion and vapour transport to the condenser.
- Model: "high-fidelity computational simulations" (Supplementary Notes 1, Figs 9-10) - a physics heat/mass-transfer model
  from the Wang group (their ref. 4 = Kim 2017 Science). Not opened in detail.
- Data form: "available within the article and its Supplementary Information or ... upon reasonable request". No repository.
- Ground-truth value: measured boundary-condition time series (T, RH, solar flux, adsorber T) in figures; the target
  (water yield) is itself a model output -> cannot serve as independent ground truth for yield.

### S09. Almassad et al. 2022, Nat. Commun. - adaptive (self-optimising) MOF-801 device, Jordan (Q1, Q2) - FETCHED (full text via Europe PMC PMC9391386; nature.com page opened)
- DOI: 10.1038/s41467-022-32642-0. Authors (Europe PMC): Almassad HA, Abaza RI, Siwwan L, Al-Maythalony B, Cordova KE. 2022.
  Licence CC BY 4.0.
- Says: "adaptive water harvesting" - an Arduino Uno controller reads an external T/RH sensor (dew point) and the dew point
  in the condensation compartment, and ends adsorption/desorption phases in real time instead of fixed timers. 400 g MOF-801
  per device; 3.5 L/kg MOF/day at 17-32% RH vs 0.7-1.3 for prior active device; 1.67-5.25 kWh/L; >1000 cycles stress test.
  Controller is a rule/threshold algorithm "developed" from historical data of the active device - NOT ML, no model.
- Data form: "Source data are provided with this paper." The nature.com page lists 41467_2022_32642_MOESM3_ESM.xlsx;
  a HEAD request (not downloaded) returned Content-Length 20,892,056 bytes. Likely contains the RH-vs-time cycle traces of
  Figs 2-5 (not verified - file not opened).
- Ground-truth value: HIGHEST found so far for device-level cycle dynamics of a MOF harvester (CC BY, machine-readable,
  multi-day, real weather). Only one material (MOF-801), and it logs air RH/dew point rather than sorbent uptake.

### S10. LaPotin et al. 2021, Joule - dual-stage zeolite harvester (Q1, Q2) - FETCHED (Crossref record + Semantic Scholar abstract)
- DOI: 10.1016/j.joule.2020.09.008. Authors (Crossref): Alina LaPotin, Yang Zhong, Lenan Zhang, Lin Zhao, Arny Leroy, Hyunho Kim, Sameer R. Rao, Evelyn N. Wang.
  Crossref issue year 2021 (online 2020). cell.com returned 403; abstract read via api.semanticscholar.org.
- Says: two stacked adsorption stages; latent heat of top-stage condensation regenerates the second stage; commercial
  zeolite AQSOA Z01 (not a MOF); ~0.77 L/m2/day outdoors under unconcentrated sun; "our modeling" predicts about 2x the
  single-stage productivity with design changes.
- Relevance: Wang-group device + physics model validated on outdoor data. Data availability not verified.

### S11. LaPotin, Kim, Rao, Wang 2019, Acc. Chem. Res. (Q2) - FETCHED (Crossref record + Semantic Scholar abstract)
- DOI: 10.1021/acs.accounts.9b00062. Authors (Crossref): Alina LaPotin, Hyunho Kim, Sameer R. Rao, Evelyn N. Wang. 2019.
- Says: equilibrium uptake from the isotherm alone is "not a good indicator" of system performance; heat- and mass-
  transport resistances in the bulk sorbent dramatically change system output; the account centres on MODELLING a
  solar-thermal system and on L/m2/day vs L/kg/day metrics.
- Relevance: the physics-model state of the art from the MIT group and the argument that a material-transfer surrogate must
  carry transport properties, not only the isotherm. Directly supports our "isotherm is not enough" framing.

### S12. Xu et al. 2021, Energy Environ. Sci. - rapid-cycling nanocomposite harvester, SJTU R.Z. Wang group (Q1) - FETCHED (Crossref record, one-line abstract only)
- DOI: 10.1039/d1ee01723c. Authors (Crossref): Jiaxing Xu, Tingxian Li, Taisen Yan, Si Wu, Minqiang Wu, Jingwei Chao, Xiangyan Huo, Pengfei Wang, Ruzhu Wang. 2021.
- Says (graphical abstract sentence only): rapid-cycling continuous solar-driven harvester with vertically aligned
  nanocomposite sorbent (salt/matrix composite, not a MOF). Numbers not verified.

### S13. Lord et al. 2021, Nature - global potential of solar AWH (Q1 context) - FETCHED (Crossref abstract)
- DOI: 10.1038/s41586-021-03900-w. Authors (Crossref): Jackson Lord, Ashley Thomas, Neil Treat, Matthew Forkin, Robert Bain, Pierre Dulac, Cyrus H. Behroozi, Tilek Mamutov, Jillia Fongheiser, Nicole Kobilansky, Shane Washburn, Claudia Truesdell, Clare Lee, Philipp H. Schmaelzle. 2021.
- Says: Google Earth Engine map for a hypothetical 1 m2 device with specific yield 0.2-2.5 L/kWh at 30-90% RH; claims AWH
  could supply safe water for a billion people. Relevant as a use case: a trained device surrogate driven by climate
  reanalysis (T, RH, irradiance) is what such a map needs; they used a fixed SY-vs-RH curve instead of a dynamic model.

### S14. Ying et al. 2025, iScience - global potential of continuous SAWH across 12 sorbents (Q2, Q4) - FETCHED (full text via Europe PMC PMC11964679; GitHub repo listed via API)
- DOI: 10.1016/j.isci.2025.112160. Authors (Crossref): Wenjun Ying, Chunfeng Li, Liang Yang, Lingji Hua, Hua Zhang, Ruzhu Wang, Jiayun Wang. 2025.
- Says: physics process models (passive and active continuous devices, rotating-sorbent designs) driven by MERRA-2 hourly
  T/RH/pressure/solar data; 12 literature sorbents incl. MOF-801, Co2Cl2(BTDD), Cr-soc-MOF-1, MCM-41-LiCl, aerogels,
  hydrogels. Kinetics = LDF with ONE uniform k per sorbent across conditions (Table S4; adsorption and desorption k separate),
  authors report dynamic-constant error within 5% across their conditions (Fig. S1). An optimiser picks the operating interval.
- Code/data: key-resources table points to https://github.com/SAWH-Ying/Continuous-SAWH-pre (Apache-2.0; created 2023,
  last push 2024-09). Repo listing shows folders Figure 3/4/5, Isotherm, evr, rad; the Isotherm folder holds only 3 small
  txt files (hydrogel/salt sorbents), NOT the MOF isotherms. README says raw MERRA-2 not uploaded. MATLAB.
- Relevance: the CLOSEST physics analogue of "cycle dynamics across materials" - a single LDF+isotherm model parameterised
  per sorbent and run over global weather. No ML, no held-out-material test, kinetics collapsed to one k per material.

### S15. Motaghian et al. 2021, Int. J. Heat Mass Transfer - ANN surrogate of a desiccant wheel (Q2) - FETCHED (Crossref record + Semantic Scholar abstract)
- DOI: 10.1016/j.ijheatmasstransfer.2020.120657. Authors (S2): Shahrooz Motaghian, Saeed Rayegan, H. Pasdarshahri, P. Ahmadi, M. Rosen (OpenAlex: Hadi Pasdarshahri, Pouria Ahmadi, Marc A. Rosen). Crossref year label 2021 (OpenAlex 2020).
- Says: ANN trained on a data bank generated from TRANSIENT physics equations; inputs = wheel design (speed, channel
  length, hydraulic diameter, area ratio, desiccant thickness, purge angle) + inlet air states; outputs = outlet T and
  humidity ratio. Best net 4 hidden layers x 50 neurons, mean relative error 0.54%; compared against experiments.
- Relevance: the standard pattern in desiccant/AHP ML - a surrogate of ONE desiccant; the sorbent is not an input, so no
  material transfer is possible or tested. Older ANN-for-wheel papers (Parmar 2011, Uckan 2014, Jani 2016) SEEN-ONLY.

### S16. Krzywanski et al. 2024, Energy Sci. Eng. - AutoML diagnostics for a 3-bed adsorption chiller (Q2) - FETCHED (Crossref abstract)
- DOI: 10.1002/ese3.1725. Authors (Crossref): Jaroslaw Krzywanski, Karol Sztekler, Dorian Skrobek, Karolina Grabowska, Waqar Muhammad Ashraf, Marcin Sosnowski, Kashif Ishfaq, Wojciech Nowak, Lukasz Mika. 2024.
- Says: DataRobot AutoML on 1769 SIMULATED points with 42 operating inputs to classify healthy vs failure states of
  components of an existing three-bed adsorption chiller/desalination plant; AUC 0.988.
- Relevance: "AI for adsorption machines" is mostly fault diagnosis / static regression on one plant; not dynamics, not
  cross-material.

### S17. Chen, Hasanien, Chua 2022, Energy Convers. Manage. - "Towards a digital twin approach" multi-bed adsorption system (Q2) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1016/j.enconman.2022.116346 (PII S0196890422011244). Authors (Crossref): W.D. Chen, Hany M. Hasanien, K.J. Chua. 2022.
- Only the title is verified (no abstract in Crossref/OpenAlex/S2; ScienceDirect 403). Treat content as UNVERIFIED; it is
  the one paper found that uses "digital twin" for an adsorption (cooling) machine.

### S18. Zheng et al. 2023, JACS - fine-tuned GPT for MOF-303 linker variants, LAMOF-1..10 (Q1, Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/jacs.3c12086. Authors (Crossref): Zhiling Zheng, Ali H. Alawadhi, Saumil Chheda, S. Ephraim Neumann, Nakul Rampal, Shengchao Liu, Ha L. Nguyen, Yen-hsu Lin, Zichao Rong, J. Ilja Siepmann, Laura Gagliardi, Anima Anandkumar, Christian Borgs, Jennifer T. Chayes, Omar M. Yaghi. 2023.
- Says: GPT fine-tuned on a linker data set proposes linker mutations; 10 isoreticular Al MOFs (LAMOF-1..10) synthesised,
  water uptake up to 0.64 g/g, step positions spanning 13-53% RH. OA copy at OSTI (purl 2510855).
- Relevance: ML for MATERIAL design (isotherm-level), not device dynamics. The 10 LAMOF isotherms (+ MOF-303, MTV-MOF-303
  series) would form a same-topology family ideal for an "unseen material" test IF the isotherms are tabulated (not verified).

### S19. Arjmandi, Aytac, Khayet, Hilal 2026, Coord. Chem. Rev. - review: ML for MOF AWH (Q2, Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1016/j.ccr.2025.217211. Authors (Crossref): M. Arjmandi, E. Aytaç, M. Khayet, N. Hilal. 2026.
- Says: reviews ML for MOF AWH discovery - RF, RFR, NCA, GA, MACE; descriptors, dataset curation challenges; highlight
  states deep learning "remains underutilized". Scope is material property prediction, not device/cycle dynamics.
- Relevance: 2026 review that (per its abstract) does not cover device-level surrogates -> supports the device-level gap.

### S20. Ahghar, Soltani, Farajollahi 2026, Water Resour. Manage. - GPR for a desiccant AWH device (Q2) - FETCHED (Springer abstract via curl)
- DOI: 10.1007/s11269-026-04790-1. Authors (Crossref): Seyed Amir Ahghar, Elshan Soltani, AmirHamzeh Farajollahi. 2026.
- Says: Gaussian Process Regression on EXPERIMENTAL data from one desiccant-driven AWH system predicts water production and
  cumulative production; DE/GA tune hyperparameters; log-transform raises R^2 to 0.981 from ~0.65; humidity, outdoor T and
  thermal regulation dominate.
- Relevance: device-level ML exists but is single-device, static regression; sorbent is not an input.

### S21. Han, Chakraborty 2025, Energy Convers. Manage. - "ML optimized adsorption heat transformations from adsorbents screening to enhanced performances" (Q2, Q3) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1016/j.enconman.2025.120272. Authors (Crossref): Bo Han, Anutosh Chakraborty. 2025.
- Title only verified; no abstract obtainable (ScienceDirect 403, S2 empty, ADS 405). Title suggests ML linking adsorbent
  screening to cycle performance of adsorption heat transformers - potentially close prior work; MUST be read before
  claiming novelty.
- SEEN-ONLY (search-engine snippet, not evidence): described as a REVIEW of ML across AHP / adsorption cooling / desalination
  / AWH / thermal storage, citing RF/NN screening of >96,000 adsorbent combinations and ML-guided cascaded MOF chillers.

### S22. Pai, Prasad, Rajendran 2020, Ind. Eng. Chem. Res. - MAPLE, adsorbent-agnostic ANN surrogate (Q3) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acs.iecr.0c02339. Authors (Crossref): Kasturi Nagesh Pai, Vinay Prasad, Arvind Rajendran. 2020.
- Says: dense feed-forward ANN (Bayesian regularisation) emulates a PSA/VSA process at CYCLIC STEADY STATE; inputs include
  adsorbent properties AND Langmuir isotherm parameters plus operating conditions; outputs purity, recovery, energy,
  productivity for "any arbitrary adsorbent"; test R2adj >= 0.995; ~2000 core-h training; optimisation per adsorbent
  from 1500 core-h to <= 1 core-min. CO2 capture case study.
- Relevance: DIRECT PRIOR ART for "a surrogate that takes the material as input". Limits: CSS KPIs only (no transient
  trajectories), Langmuir (type I) parameterisation, gas separation, pressure swing.

### S23. Pai, Nguyen, Prasad, Rajendran 2022, Sep. Purif. Technol. - experimental validation of the adsorbent-agnostic ANN on UNSEEN adsorbents (Q3) - FETCHED (Crossref record; abstract from OpenAlex record of the chemRxiv preprint 10.26434/chemrxiv-2021-26xgh)
- DOI: 10.1016/j.seppur.2022.120783. Authors (Crossref): Kasturi Nagesh Pai, Tai T.T. Nguyen, Vinay Prasad, Arvind Rajendran. 2022.
- Says (preprint abstract): surrogate trained on 20,000 detailed-model runs over HYPOTHETICAL Langmuir parameters + particle
  density, porosity, bed voidage + process variables (Skarstrom VSA, O2 from air). Then used with measured N2/O2 isotherms of
  zeolites 13X and LiX - the abstract states these isotherms were not part of the training data - for multi-objective
  optimisation; 9 Pareto points run on a two-column rig; mean |error| purity 3%, recovery 5%, productivity 9%.
- VERDICT FOR OUR GAP CLAIM: "transfer of an adsorption-process surrogate to materials it was not trained on" HAS BEEN DONE
  AND EXPERIMENTALLY VALIDATED, for gas PSA/VSA at the CSS-KPI level. Our paper must not claim first-ever material transfer.
  What remains open (not found): transient/dynamic trajectories, water (type IV/V stepped, hysteretic) isotherms,
  temperature-swing/solar-driven water harvesting, MOF/COF water kinetics, and a measured held-out-MATERIAL test on dynamics.
  Caveat: "unseen" there = unseen isotherm but inside the sampled Langmuir parameter box (interpolation in parameter space).

### S24. Subraveti, Li, Prasad, Rajendran 2022, Ind. Eng. Chem. Res. - PANACHE physics-constrained NNs for cyclic adsorption (Q3) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acs.iecr.1c04731 (preprints chemRxiv 10.26434/chemrxiv-2021-lm2sl, -v2). Authors (Crossref): Sai Gokul Subraveti, Zukui Li, Vinay Prasad, Arvind Rajendran. 2022.
- Says: deep NNs with a physics-constrained loss (governing PDEs) predict full spatiotemporal column states for each
  constituent step (pressurisation, adsorption, blowdown, evacuation...) under step-specific boundary conditions; four VSA
  cycles assembled WITHOUT retraining; 50 simulations per cycle to CSS; purity/recovery within 2.5% of detailed model;
  ~100x speed-up. Abstract says no system-specific inputs such as isotherm parameters are required.
- Relevance: closest analogue to "learning cycle dynamics" (spatiotemporal, cycle synthesis). Material transfer is NOT
  claimed in the abstract (not verified from full text whether a new isotherm needs retraining).

### S25. Burns et al. 2020, Environ. Sci. Technol. - 1632 MOFs through a validated VSA simulator + ML (Q3, Q4) - FETCHED (Crossref abstract)
- DOI: 10.1021/acs.est.9b07407. Authors (Crossref): Thomas D. Burns, Kasturi Nagesh Pai, Sai Gokul Subraveti, Sean P. Collins, Mykhaylo Krykunov, Arvind Rajendran, Tom K. Woo. 2020.
- Says: GCMC isotherms for 1632 experimentally characterised MOFs fed into a pilot-validated VSA simulator; 482 meet 95/90
  purity/recovery; ML classifier on common adsorption metrics predicts meeting the target with 91% accuracy; accurate
  energy/productivity need full process simulation.
- Relevance: template for "process-informed screening across many MOFs" - but CO2, simulated isotherms, CSS metrics.

### S26. Pai, Prasad, Rajendran 2020, Sep. Purif. Technol. - ML surrogates for PSA CSS, validated on a 2-column rig (Q3) - FETCHED (Crossref + Semantic Scholar abstract)
- DOI: 10.1016/j.seppur.2020.116651. Authors (Crossref): Kasturi Nagesh Pai, Vinay Prasad, Arvind Rajendran. 2020.
- Says: GPR best for KPIs from 400 sampled operating conditions (R2adj > 0.98); ANN predicts CSS bed profiles; experiments on
  zeolite 13X (CO2/N2) confirm; surrogate optimisation ~23x faster, CSS-initialised detailed optimisation ~6x faster.
- Relevance: single-material surrogate (13X); shows CSS profile prediction exists.

### S27. Rajendran, Subraveti, Pai, Prasad, Li 2023, Acc. Chem. Res. (Q3) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acs.accounts.3c00335. Authors (Crossref): Arvind Rajendran, Sai Gokul Subraveti, Kasturi Nagesh Pai, Vinay Prasad, Zukui Li. 2023.
- Says: argues adsorbent performance is tied to the process; summarises MAPLE (process + material inputs, experimentally
  validated), practically achievable PVSA limits, and PINNs for cycle configuration.
- Relevance: authoritative summary of the "material-as-input process surrogate" line. Cite with S22/S23.

### S28. Kim, Rubiera Landa, Ravutla, Realff, Boukouvala 2022, Chem. Eng. Res. Des. (Q3) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1016/j.cherd.2022.10.002. Authors (Crossref): Sun Hye Kim, Héctor Octavio Rubiera Landa, Suryateja Ravutla, Matthew J. Realff, Fani Boukouvala. 2022.
- Title: data-driven simultaneous process optimisation and adsorbent selection for VPSA. Abstract not obtained -> content
  unverified; title implies adsorbent choice inside a surrogate optimisation (another material-as-input precedent).

### S29. Ceccanti, Galanti, Roghair, van Sint Annaland 2026, arXiv:2601.09491 - DeepONets for cyclic (TVSA) adsorption (Q3) - FETCHED (arXiv API abstract)
- arXiv 2601.09491v1, submitted 2026-01-14. Authors (arXiv): Beatrice Ceccanti, Mattia Galanti, Ivo Roghair, Martin van Sint Annaland.
- Says: DeepONet maps a step's INITIAL CONDITION (the previous step's final state) to the transient solution field, aiming to
  accelerate TVSA cycle convergence; steep travelling fronts; mixed training set of heterogeneous initial conditions; tested
  on initial conditions outside training ranges and on unseen functional forms, reporting accurate predictions in and out
  of distribution.
- Relevance: the closest NEURAL-OPERATOR prior work for cyclic adsorption. Generalisation axis = initial condition, NOT
  sorbent material (abstract does not mention varying isotherms/materials).

### S30. Galanti et al. 2025, Processes - hybrid PINNs vs NNs for DAC adsorption step (Q3) - FETCHED (Crossref abstract)
- DOI: 10.3390/pr13092824 (preprint chemRxiv 10.26434/chemrxiv-2025-1rqnx). Authors (Crossref): Mattia Galanti, Mik Janssen, Ivo Roghair, Jean-Yves Dieulot, Pejman Shoeibi Omrani, Jurriaan Boon, Martin van Sint Annaland. 2025.
- Says: hybrid-PINNs beat plain NNs in intermediate/low-data regimes for the DAC adsorption step; curriculum learning for
  extreme low data; PINN training ~10x more expensive. Single sorbent/process; no material transfer.

### S31. Wu et al. 2025, Green Chem. Eng. - physics-informed ML + transfer learning for PSA (Q3) - FETCHED (Crossref record + OpenAlex abstract)
- DOI: 10.1016/j.gce.2024.08.004. Authors (Crossref): Zhiqiang Wu, Yunquan Chen, Bingjian Zhang, Jingzheng Ren, Qinglin Chen, Huan Wang, Chang He. Crossref year 2025 (OpenAlex 2024).
- Says: five sub-networks for the five PSA steps; "parameter-based transfer learning" with domain decomposition to handle
  long-time integration of periodic PDEs; labelled data added at boundaries to handle sharp fronts; matches numerical solver.
- Relevance: "transfer learning" here is across TIME WINDOWS/steps, not across materials. Do not confuse with our claim.

### S32. Dhamanekar et al. 2025, arXiv:2502.02268 - "simplified digital twin" of an O2 PSA plant (Q2, Q3) - FETCHED (arXiv API abstract)
- Authors (arXiv): Abhijit Dhamanekar, Ritwik Das, Santosh Ansumali, Raviraju Vysyaraju, Arvind Rajendran, Diwakar S. V. Submitted 2025-02-04.
- Says: axisymmetric CFD model of the whole plant (reservoir, columns, buffer tank, valves) with adsorption kinetics;
  switching emulated by boundary-condition changes; reproduces pilot purity and pressure transients; numerical and
  experimental optima coincide (pressurisation 26 s, purge 2 s, equalisation 4 s).
- Relevance: shows "digital twin" in adsorption is currently used for PHYSICS (CFD) replicas of one plant, not learned
  cross-material models.

### S33. Zhang, Zhou, Sundmacher 2022, AIChE J. - integrated MOF + P/VSA design, "MOF matching" (Q3) - FETCHED (Crossref abstract)
- DOI: 10.1002/aic.17788. Authors (Crossref): Xiang Zhang, Teng Zhou, Kai Sundmacher. 2022.
- Says: optimise MOF descriptors + operating conditions jointly, then find real/hypothetical MOFs (building blocks from 471
  CoRE MOFs -> 45,472 hypothetical) matching the optimum; propene/propane. Material-as-descriptor process design precedent.

### S34. Calvo-Schwarzwalder et al. 2026, arXiv:2607.17941 - PFO kinetics unfit for column dynamics (Q3 risk) - FETCHED (arXiv API abstract)
- Authors (arXiv): M. Calvo-Schwarzwalder, A. Valverde, A. Cuesta López, A. Cabrera-Codony, U. Thorat, T. G. Myers. 2026-07-20.
- Says: PFO+Sips column model predicts an abrupt breakthrough, underperforms pure Sips against literature data; authors call
  PFO "inherently flawed" for column dynamics. Relevance: a warning for any model (ours included) that relies on a first-order
  / LDF-type rate law as ground truth; LDF (solid-film) differs from PFO but the critique should be checked before we lean
  on LDF for water in MOFs.

### S35. NIST/ARPA-E Database of Novel and Emerging Adsorbent Materials (ISODB) - water content audited via its public API (Q4) - FETCHED (API queried 2026-09-25)
- URLs opened: https://adsorption.nist.gov/isodb/index.php (JS app; disclaimer text only), https://adsorption.nist.gov/isodb/api/gases.json,
  https://adsorption.nist.gov/isodb/api/isotherms.json (full index streamed, not stored in repo), https://adsorption.nist.gov/matdb/api/materials.json,
  https://adsorption.nist.gov/isodb/api/isotherm/10.1021ja500330a.Isotherm1.json (one record opened).
- Counts I computed from the index (water InChIKey XLYOFNOQVPJJNP-UHFFFAOYSA-N): 39,988 isotherms total; 2,455 involve water;
  1,221 are PURE-water isotherms covering 557 adsorbent records from 275 DOIs. Category field: 413 "exp", 98 "sim",
  10 "mod", 700 blank. Only 61 of 1,221 flagged tabular_data=1 (i.e. ~95% were digitised from figures). Temperatures mostly
  298 K (635), then 300/293/303 K; few at >= 323 K.
- Coverage spot-checks (name search): CuBTC 79, ZIF-8 42, Mg-MOF-74 40, zeolite 13X 26, silica gel 25, UiO-66 family 31,
  MIL-101 family 20, CAU-10 family 17, MIL-160 11, Al-fumarate 8, MOF-801 3, AQSOA-FAM-Z02 3, ~30 COF entries
  (AB-COF, ATFG-COF, TTCOF-*, COF-42, TPB-BPTA-COF variants...). ABSENT: MOF-303, Co2Cl2(BTDD), SAPO-34, COF-432, and the
  water-harvesting papers (Kim 2017, Fathieh 2018, Hanikel 2019/2021, Nguyen 2020 not indexed). Furukawa 2014 is indexed
  but only 12 isotherms (11 materials) at 298 K, not all 23 materials.
- Record format: JSON with pressure (bar) and uptake (e.g. cm3(STP)/g) points, adsorbent hashkey, DOI; interoperable with
  MOFX-DB. Licence: page states "(c)2016 ... All rights reserved" and portions collected with SpringerMaterials support ->
  redistribution terms UNCLEAR; cite and re-download rather than redistribute.
- Verdict: usable seed for many real sorbents' water isotherms at ~298 K; weak for temperature dependence (needed for TSA)
  and missing the flagship harvesting MOFs/COFs. Digitisation noise must be expected.

### S36. Furukawa et al. 2014, JACS - water adsorption in 23 materials incl. 20 MOFs (Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/ja500330a. Authors (Crossref): Hiroyasu Furukawa, Felipe Gándara, Yue-Biao Zhang, Juncong Jiang, Wendy L. Queen, Matthew R. Hudson, Omar M. Yaghi. 2014.
- Says: criteria for water sorbents (condensation pressure in pores, capacity, recyclability/stability); 23 materials, 20 MOFs,
  10 Zr MOFs (MOF-801-SC/-P, -802, -805, -806, -808, -841...); MOF-801-P and MOF-841 best; 5-cycle stability.
- Relevance: the largest single-lab, same-protocol experimental water-isotherm set for MOFs; partially in ISODB (S35).

### S37. Bobbitt et al. 2023, J. Chem. Eng. Data - MOFX-DB (Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acs.jced.2c00583. Authors (Crossref): N. Scott Bobbitt, Kaihang Shi, Benjamin J. Bucior, Haoyuan Chen, Nathaniel Tracy-Amoroso, Zhao Li, Yangzesheng Sun, Julia H. Merlin, J. Ilja Siepmann, Daniel W. Siderius, Randall Q. Snurr. 2023.
- Says: >3 million SIMULATED adsorption points for H2, CH4, CO2, Xe, Kr, Ar, N2 in >160,000 MOFs and 286 zeolites; JSON
  compatible with NIST ISODB. WATER IS NOT in the listed adsorbates -> MOFX-DB is not a water-isotherm source.

### S38. Ongari, Talirz, Jablonka, Siderius, Smit 2022, J. Chem. Eng. Data (Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acs.jced.1c00958. Authors (Crossref): Daniele Ongari, Leopold Talirz, Kevin Maik Jablonka, Daniel W. Siderius, Berend Smit. 2022.
- Says: automatic linking of ISODB isotherms to CSD crystal structures; 545 Ar/N2 isotherms matched; measured vs geometric
  pore volume agree in only ~35% of cases.
- Relevance: tooling to join ISODB water isotherms to structures (for descriptors of "unseen" MOFs); and a warning that
  experimental sample quality varies strongly - material-to-material noise will be large.

### S39. Zhao et al. 2025, Matter - CoRE MOF DB (2024 version) (Q4, Q3) - FETCHED (Crossref record + OpenAlex abstract of chemRxiv 10.26434/chemrxiv-2024-nvmnr-v2)
- DOI: 10.1016/j.matt.2025.102140. Authors (Crossref): Guobin Zhao, Logan M. Brabson, Saumil Chheda, Ju Huang, Haewon Kim, Kunhuan Liu, Kenji Mochida, Thang D. Pham, Prerna, Gianmarco G. Terrones, Sunghyun Yoon, Lionel Zoubritzky, François-Xavier Coudert, Maciej Haranczyk, Heather J. Kulik, Seyed Mohamad Moosavi, David S. Sholl, J. Ilja Siepmann, Randall.Q. Snurr, Yongchul G. Chung. 2025.
- Says: curated computation-ready experimental MOF structures; ML-predicted stability and heat capacity; ML DDEC charges;
  Gibbs-ensemble MC to CLASSIFY hydrophobicity (not full water isotherms); integrated material-process screening with
  high-fidelity TSA simulations for carbon capture.
- Relevance: gives structures/descriptors and a hydrophobic/hydrophilic label for real MOFs; another "material-process
  screening" precedent (CO2 TSA). Not a water-isotherm or kinetics dataset.

### S40. Shih, Lin 2025, JACS - simulated water adsorption in >200 MOFs (Q4) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/jacs.5c10686. Authors (Crossref): Shiue-Min Shih, Li-Chiang Lin. 2025. (OpenAlex shows the first author as
  "Shang-Chuan Shih" - records disagree; use Crossref and re-check on the article page before citing.)
- Says: molecular simulation of water adsorption in >200 selected MOFs; subtypes of S-shaped/non-S-shaped isotherms;
  moderate heat of adsorption needed for S-shape; pore size sets step steepness; site density/uniformity set step pressure.
- Relevance: potential SIMULATED water-isotherm set for >200 real MOFs if deposited (not verified). Useful for physics priors
  on step position/steepness.

### S41. Nguyen, Gropp, Hanikel, Möckel, Lund, Yaghi 2022, ACS Cent. Sci. - hydrazine-hydrazide-linked COFs (Q5) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/acscentsci.2c00398. Authors (Crossref): Ha L. Nguyen, Cornelius Gropp, Nikita Hanikel, Anna Möckel, Alicia Lund, Omar M. Yaghi. 2022.
- Says: postsynthetic partial oxidation gives irreversible hydrazide linkages; one COF has S-shaped isotherm with steep step
  below 18% RH at 25 C and 0.45 g/g total uptake; small molecular changes shift isotherms strongly. Isotherm-level only.

### S42. Sun et al. 2023, Angew. Chem. Int. Ed. - DHTA-Pa COF, fast kinetics (Q5, Q4 kinetics) - FETCHED (Crossref abstract)
- DOI: 10.1002/anie.202217103. Authors (Crossref): Chao Sun, Yuhao Zhu, Pengpeng Shao, Liwei Chen, Xin Huang, Shuang Zhao, Dou Ma, Xuechun Jing, Bo Wang, Xiao Feng. 2023.
- Says: 0.48 g/g at 30% RH; adsorption rate 0.72 L/kg/h at 298 K, desorption 2.58 L/kg/h at 333 K; >90% released within
  20 min at 313 K; attributes speed to hydrophobic skeleton + moderate hydrophilic site density + 1D channels.
- Relevance: one of few COF papers reporting uptake RATES -> a candidate COF kinetic curve (figures only, not verified).

### S43. Grunenberg et al. 2023, JACS - nitrone-linked COFs (Q5) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1021/jacs.3c02572. Authors (Crossref): Lars Grunenberg, Gökcen Savasci, Sebastian T. Emmerling, Fabian Heck, Sebastian Bette, Afonso Cima Bergesch, Christian Ochsenfeld, Bettina V. Lotsch. 2023.
- Says: postsynthetic imine/amine -> nitrone conversion (NO-PI-3-COF, NO-TTI-COF) shifts water condensation to ~20% lower
  humidity than precursors. Isotherm-level; OA in PMC (PMC10288504).

### S44. Nguyen et al. 2025, ACS Cent. Sci. - hydrophilicity index predicting isotherm step from structure, COFs + MOFs (Q5, Q4) - FETCHED (Crossref record + Europe PMC abstract, PMC12123544)
- DOI: 10.1021/acscentsci.4c01878. Authors (Crossref): Ha L. Nguyen, Andrea Darù, Saumil Chheda, Ali H. Alawadhi, S. Ephraim Neumann, Lifen Wang, Xuedong Bai, Majed O. Alawad, Christian Borgs, Jennifer T. Chayes, Joachim Sauer, Laura Gagliardi, Omar M. Yaghi. 2025.
- Says: 2D COFs HCOF-2, HCOF-3 and new COF-309 for high working capacity at low RH; a "hydrophilicity index" from strength
  and spatial density of adsorptive sites is mathematically correlated with the isotherm step and extended to other
  microporous COFs and MOFs.
- Relevance: a physically meaningful, structure-derived MATERIAL DESCRIPTOR for water-step position covering both COFs and
  MOFs - exactly the kind of input a cross-material dynamics model needs. Isotherm step only; no kinetics/device.

### S45. Nguyen 2023, Adv. Mater. - review "COFs for AWH" (Q5) - FETCHED (Crossref abstract)
- DOI: 10.1002/adma.202300018. Author (Crossref): Ha L. Nguyen. 2023. Review of design features and achievements of
  water-harvesting COFs; material chemistry focus.

### S46. Wen, Huang 2024, ChemSusChem - review "COFs for water harvesting from air" (Q5) - FETCHED (Crossref abstract)
- DOI: 10.1002/cssc.202400049. Authors (Crossref): Fuxiang Wen, Ning Huang. 2024. Summarises isotherm descriptors and
  mechanisms, preparation of COF water harvesters; lists needs: working capacity, rapid kinetics, low energy, stability.

### S47. He et al. 2025, Environ. Sci.: Water Res. Technol. - review "COFs enable efficient AWH in arid climates" (Q5) - FETCHED (Crossref one-line abstract; S2 truncated abstract)
- DOI: 10.1039/d5ew00643k. Authors (Crossref): Yuan He, Jiaqi Ran, Xiaoting Gao, Jimeng Ding, Michael R. Templeton, Cheng Peng, Wenhai Chu. 2025.
- Says: review of COF-based AWH trends under arid conditions. SEEN-ONLY (search snippet): mentions ML + computational
  chemistry as a future direction for COF screening -> consistent with "no COF-specific ML/modelling yet".

### S48. Chen et al. 2025, Chem. Eng. J. - anionic 2D COF (TpPa-2SO3Li) (Q5) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1016/j.cej.2025.171055. Authors (Crossref): Zhenhui Chen, Jingsong Feng, Yanpeng Cui, Daochuan Jiang, Yue Lin, Leyang Guo, Junjie Zhang, Yang Yang, Daolun Feng, Zhifu Liang. 2025.
- SEEN-ONLY (search snippet, not evidence): 0.74 g/g at 30% RH, 25 C; desorption at 60 C; device up to 3.27 L/kg/day at
  50-80% RH. Salt-like ionic COF, humid rather than arid conditions. Verify before citing numbers.

### S49. Li, Shi, Liang, Liu, Qiao 2022, Nanomaterials - ML-assisted GCMC screening of CoRE/hMOFs for H2O capture from air (Q4) - FETCHED (Europe PMC abstract, PMC8746952)
- DOI: 10.3390/nano12010159. Authors (Europe PMC): Li L, Shi Z, Liang H, Liu J, Qiao Z. 2022.
- Says: GCMC H2O/N2/O2 for 6013 CoRE MOFs and 137,953 hMOFs; Qst dominant descriptor; RF/GBRT/NCA, NCA R2 0.97 on CoRE,
  transfers to hMOFs with R2 0.86. Equilibrium selectivity only, no kinetics, no process. Shows cross-set transfer is
  routinely weaker (0.97 -> 0.86) even at the isotherm level.

### S50. Cho et al. 2020, Nat. Commun. - KMF-1 Al-MOF for water-sorption heat allocation, G-LTJ kinetics (Q4 kinetics, Q2) - FETCHED (full text via Europe PMC PMC7547100)
- DOI: 10.1038/s41467-020-18968-7. Authors (Europe PMC): Cho KH, Borges DD, Lee UH, Lee JS, Yoon JW, Cho SJ, Park J, Lombardo W, Moon D, Sapienza A, Maurin G, Chang JS. 2020.
- Says: KMF-1 found by joint computation + experiment; step isotherm; COP 0.75 cooling / 1.74 heating; driving T < 70 C.
  Kinetics by gravimetric Large Temperature Jump (G-LTJ) on shaped granules at several boundary conditions (Supp. Fig. 25,
  Table 11); characteristic time tau, SCP/SHP; kinetics compared with Co-CUK-1 and MOF-303 (Supp. Fig. 21: KMF-1 and MOF-303
  equivalent rates under the same conditions).
- Data form: CCDC structures deposited; "further data ... available from the corresponding author upon reasonable request".
  Kinetic curves in SI figures only.
- Relevance: LTJ is the standard AHT kinetic protocol (Aristov / CNR-ITAE Sapienza line); kinetic curves exist for several
  MOFs but scattered across SI figures of separate papers, with different grain sizes/configurations.

### S51. de Lange, Verouden, Vlugt, Gascon, Kapteijn 2015, Chem. Rev. - adsorption-driven heat pumps, MOF potential (Q2, Q4) - FETCHED (Crossref record; OpenAlex "abstract" is page chrome only)
- DOI: 10.1021/acs.chemrev.5b00059. Authors (Crossref): Martijn F. de Lange, Karlijn J. F. M. Verouden, Thijs J. H. Vlugt, Jorge Gascon, Freek Kapteijn. 2015.
- Content NOT verified beyond title (known as the reference thermodynamic screening of MOF water isotherms for AHP - treat as unverified).

### S52. Zhang, Zhu, Wang, Liu, Kapteijn 2024, Adv. Funct. Mater. - review "Water adsorption in MOFs: structures and applications" (Q4, Q5) - FETCHED (Crossref abstract)
- DOI: 10.1002/adfm.202304788. Authors (Crossref): Bo Zhang, Zerui Zhu, Xuerui Wang, Xinlei Liu, Freek Kapteijn. 2024.
- Says: six selection criteria identify ~40 reported MOFs and ONE COF as candidates for water applications; "No-MOF-fits-all"
  (step location must match application); most applications bench/small-pilot; TEA/LCA needed.
- Relevance: a ready shortlist (~40 MOFs + 1 COF) for a real-materials dataset; confirms how thin the COF side is.

### S53. Meunier 2017, Science - Technical Comment on Kim et al. 2017 (Q1 skepticism) - FETCHED (Crossref abstract)
- DOI: 10.1126/science.aao0361. Author (Crossref): Francis Meunier. 2017.
- Says: the process as described is inadequate and "cannot deliver the claimed amount" of liquid water in an arid climate;
  suggests process redesign and more suitable MOFs.

### S54. Bui, Chua, Gordon 2017, Science - Technical Comment on Kim et al. 2017 (Q1 skepticism) - FETCHED (Crossref abstract)
- DOI: 10.1126/science.aao0791. Authors (Crossref): Duc Thuan Bui, Kian Jon Chua, Jeffrey M. Gordon. 2017.
- Says: basic thermodynamics and off-the-shelf alternatives show the approach is "vastly inferior in efficiency".
- Relevance for us: early headline MOF-harvester numbers were projections from models; a digital-twin paper must separate
  measured from modelled yield in every dataset it uses (see S08 as well).

### S55. Dubai RDI Program grant page - "AI-Enabled Digital-Twin Design of Solar-Powered AWH System" (Q2 competitor watch) - FETCHED (web page)
- URL: https://dubairdi.ae/grant-initiatives-the-ai-enabled-digital-twin-design-of-solar-powered-atmospheric-water-harvesting-system-for-clean-and-reliable-water-solutions/
- Says: funded project (Dubai Research, Development and Innovation Program / Dubai Future Foundation); PI listed as
  Dr. Anang Amin, Higher Colleges of Technology; MOF sorbent + thermoelectric condensation + AI control + digital twin for
  predictive maintenance. No dates or outputs listed.
- Relevance: someone is funded to build an "AI digital twin of a MOF AWH system" - a naming/priority risk for our title,
  though the page describes a single engineered system with TEC condensation, not cross-material learning.

### S56. Bezrukov et al. 2023, Cell Rep. Phys. Sci. - seven MOFs + Syloid, AWH sorption KINETICS, cycle simulation, open DVS data + code (Q1, Q2, Q4) - FETCHED (Crossref + OpenAlex abstract; Zenodo API record; GitHub API + README + code files)
- DOI: 10.1016/j.xcrp.2023.101252. Authors (Crossref): Andrey A. Bezrukov, Daniel J. O’Hearn, Victoria Gascón-Pérez, Shaza Darwish, Amrit Kumar, Suresh Sanda, Naveen Kumar, Kurt Francis, Michael J. Zaworotko. 2023.
- Says (abstract): AWH kinetics of seven known MOFs and the industry desiccant Syloid are limited by diffusion to the
  sorbent BED SURFACE (not intracrystalline); a quantitative model "that exploits isotherm shape" simulates sorption cycling
  and gives productivity heatmaps; steady-state oscillation around PARTIAL loading maximises productivity; dense
  ultramicroporous MOFs with a low-RH step win volumetrically for 27 C/30% RH <-> 60 C/5.4% RH swings; cellulose composites
  of two such sorbents keep powder kinetics, up to 7.3 L/kg/day under these (lab) conditions.
- Data: Zenodo 10.5281/zenodo.6631711 (record opened via API): "data.zip", 606,719,336 bytes, CC-BY-4.0, isSupplementTo the
  article. NOT downloaded. Code: https://github.com/AndreyBezrukov/Water_Sorption_Kinetics (Jupyter/Python; NO licence file
  per GitHub API; last push 2023-01-12). analyze_kinetics.py parses raw DVS instrument exports (DVS Intrinsic, DVS
  Advantage Plus, DVS Vacuum) into time, uptake, RH_target, RH_actual, temp_target, temp_actual -> the Zenodo archive is RAW
  uptake-vs-time data. Notebooks reference ROS-037, ROS-039, ROS-040, MOF-303, Al-fumarate, MIL-160, CAU-10-H and Syloid
  (my reading of the notebook strings; I infer these are the 7 MOFs + Syloid - confirm in the paper). Also an OA copy at
  University of Limerick figshare (10.34961/researchrepository-ul.22847069.v1, per OpenAlex; not opened).
- VERDICT: this is simultaneously (a) the best open multi-material water-kinetics dataset found, and (b) the CLOSEST PRIOR
  WORK to "learning cycle dynamics across materials": a single physics model, parameterised by each material's isotherm,
  simulating cycling for 8 sorbents under a shared protocol. It is not ML and does not test held-out materials, but any
  claim that "cross-material cycle dynamics" is unstudied is false.

### S57. Ortiz, Rao 2024, Cell Rep. Phys. Sci. - compact rapid-cycling fuel-fired Al-fumarate harvester (Q1, Q2) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1016/j.xcrp.2024.102115. Authors (Crossref): Nathan P. Ortiz, Sameer R. Rao. 2024.
- Says: aluminium-fumarate MOF packed in a compact adsorbent heat exchanger (AHX) with fuel combustion heating and an
  ambient-cooled condenser for continuous daily cycling; a COMPUTATIONAL MODEL optimises adsorption truncation (partial
  loading) and sorbent-fin thickness; reports 3.19 kg water/kg MOF/day or 718 kg/m3 AHX/day "can be achieved"
  (wording suggests model-projected, 1.5x/2.1x over prior MOF multi-cycle devices without refrigeration).
- Relevance: Rao-group physics model + optimisation of cycle truncation - the control variable a learned twin would
  optimise. Same "partial loading is optimal" message as S56. Data availability not verified.

### S58. Young, Mcilwaine, Smit, Garcia, van der Spek 2023, Chem. Eng. J. - process-informed DAC sorbent guidelines (Q3) - FETCHED (Crossref + OpenAlex abstract)
- DOI: 10.1016/j.cej.2022.141035. Authors (Crossref): John Young, Fergus Mcilwaine, Berend Smit, Susana Garcia, Mijndert van der Spek. Crossref year 2023 (OpenAlex 2022).
- Says: detailed TVSA/S-TVSA process model + ML + global sensitivity over ALL model parameters (material + operating):
  dry CO2 capacity does not matter for TVSA; KINETICS, density and thermal conductivity are critical; heat transfer matters.
- Relevance: strong external support for our premise that isotherm alone does not determine cycle performance; material
  properties varied as continuous inputs (hypothetical sorbents), not real held-out materials.

### S59. Charalambous et al. 2024, Nature - PrISMa platform (Q3) - FETCHED (Crossref abstract)
- DOI: 10.1038/s41586-024-07683-8. Authors (Crossref): Charithea Charalambous, Elias Moubarak, Johannes Schilling, Eva Sanchez Fernandez, Jin-Yu Wang, Laura Herraiz, Fergus Mcilwaine, Shing Bo Peh, Matthew Garvin, Kevin Maik Jablonka, Seyed Mohamad Moosavi, Joren Van Herck, Aysu Yurdusen Ozturk, Alireza Pourghaderi, Ah-Young Song, Georges Mouchaham, Christian Serre, Jeffrey A. Reimer, André Bardow, Berend Smit, Susana Garcia. 2024.
- Says: integrates materials, process design, techno-economics and LCA; >60 CO2 case studies in 5 regions.
- Relevance: the state of the art for material -> process -> impact pipelines is in CO2 capture, at Nature level. A water-
  harvesting analogue (materials -> cycle dynamics -> L/kg/day under real climates) does not appear to exist; S14 (Ying) and
  S56 (Bezrukov) are the partial analogues.

### S60. Hong, Park, Chung, Heo, Kim 2026, Appl. Therm. Eng. - physics-based digital twin of a MOF desiccant dehumidifier for fault detection (Q2) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1016/j.applthermaleng.2026.132018. Authors (Crossref): Seong Ho Hong, Myeong Hyeon Park, Jun Yeob Chung, Juneyeong Heo, Yongchan Kim. 2026.
- Title only verified (no abstract in Crossref/OpenAlex/S2). Title says: PHYSICS-based digital twin, real-time fault
  detection/diagnosis, desiccant dehumidification with MOFs. This is the nearest "MOF + digital twin" paper found; it is
  for dehumidification (HVAC), physics-based, fault-oriented. Must be read before our paper uses "digital twin of a MOF
  sorption device" as a novelty claim.

### S61. Tariq, Ali, Sheikh, Shahzad, Xu 2023, Int. Commun. Heat Mass Transf. - ANN "digital twin" of a desiccant cooling system (Q2) - FETCHED (Crossref record + OpenAlex abstract)
- DOI: 10.1016/j.icheatmasstransfer.2022.106538. Authors (Crossref): Rasikh Tariq, Muzaffar Ali, Nadeem Ahmed Sheikh, Muhammad Wakil Shahzad, Ben Bin Xu. Crossref year 2023 (OpenAlex 2022).
- Says: small ANNs (5-[6]-[6]-1, 5-[12]-[12]-1) trained on monitored transient data of one real desiccant cooling system in
  Austria (inputs ambient T, humidity, regeneration T, supply/return flow) predict cooling capacity and water footprint
  (R2 0.989 / 0.992); the white-box ANN is called a "digital twin"; GA + MCDA optimisation.
- Relevance: typical use of "digital twin" in sorption HVAC = static ANN regression of one plant. Single desiccant.

### S62. CoRE MOF 2024 dataset on Zenodo (companion to S39) - simulated water isotherms for real MOF structures (Q4) - FETCHED (Zenodo API record 15055758)
- DOI: 10.5281/zenodo.15055758, "Computation-Ready Experimental Metal-Organic Framework (CoRE MOF) 2024 Dataset",
  2025-03-20 version, CC-BY-4.0; creators start Zhao, Guobin; Brabson, Logan M.; Chheda, Saumil; ...
- Record says: public "CoRE MOF SI" set = 2,664 computation-ready + 5,636 not-computation-ready structures (full DB 40,837
  incl. CSD-derived, which need a CCDC licence); precomputed properties include pore metrics, density, topology, open metal
  sites, DDEC charges, heat capacity, decomposition T, probability of water stability, hydrophobic class from GEMC.
  Files include "water.zip" (12,521,561 bytes) described as "GEMC water isotherm data of CR dataset", and "TSA.zip"
  (271,657,136 bytes; single isotherms of 35 MOFs used in TSA plus TSA results). NOT downloaded.
- Verdict: the largest openly licensed set of WATER isotherms on real MOF structures found - but SIMULATED (Gibbs-ensemble
  MC, rigid frameworks, force-field dependent), at unverified temperatures/RH grid; water isotherms from GEMC are known to be
  force-field sensitive. Good for pre-training / priors; not ground truth for kinetics or devices.


---------------------------------------------------------------------------------------------------------------------

## Fetched-source table

Depth codes: FT = full text read (Europe PMC / PDF); AB = abstract read (Crossref/OpenAlex/S2/arXiv/publisher);
MD = metadata only (title/authors/year confirmed, content NOT verified); DS = dataset/code record opened (Zenodo/GitHub/API);
WEB = web page read. SEEN-ONLY items are flagged inside the entries and are not evidence.

| ID | Year | First author (as fetched) | DOI / URL opened | Q | Depth |
|---|---|---|---|---|---|
| S01 | 2025 | Nobel press release | nobelprize.org/prizes/chemistry/2025/press-release/ | 6 | WEB |
| S02 | 2017 | Hyunho Kim | 10.1126/science.aam8743 | 1 | AB |
| S03 | 2018 | Farhad Fathieh | 10.1126/sciadv.aat3198 | 1 | FT |
| S04 | 2019 | Nikita Hanikel | 10.1021/acscentsci.9b00745 | 1,4 | FT |
| S05 | 2021 | Nikita Hanikel | 10.1126/science.abj0890 (+ Zenodo 5294977) | 1,4 | AB+DS |
| S06 | 2020 | Ha L. Nguyen | 10.1021/jacs.9b13094 | 1,5 | AB |
| S07 | 2023 | Woochul Song | 10.1038/s44221-023-00103-7 ; Zenodo 10.5281/zenodo.7990951 | 1 | FT+DS |
| S08 | 2018 | Kim H (Europe PMC) | 10.1038/s41467-018-03162-7 | 1,2 | FT |
| S09 | 2022 | Almassad HA (Europe PMC) | 10.1038/s41467-022-32642-0 | 1,2 | FT (+HEAD of Source Data) |
| S10 | 2021 | Alina LaPotin | 10.1016/j.joule.2020.09.008 | 1,2 | AB |
| S11 | 2019 | Alina LaPotin | 10.1021/acs.accounts.9b00062 | 2 | AB |
| S12 | 2021 | Jiaxing Xu | 10.1039/d1ee01723c | 1 | AB (one line) |
| S13 | 2021 | Jackson Lord | 10.1038/s41586-021-03900-w | 1 | AB |
| S14 | 2025 | Wenjun Ying | 10.1016/j.isci.2025.112160 ; github.com/SAWH-Ying/Continuous-SAWH-pre | 2,4 | FT+DS |
| S15 | 2021 | Shahrooz Motaghian | 10.1016/j.ijheatmasstransfer.2020.120657 | 2 | AB |
| S16 | 2024 | Jaroslaw Krzywanski | 10.1002/ese3.1725 | 2 | AB |
| S17 | 2022 | W.D. Chen | 10.1016/j.enconman.2022.116346 | 2 | MD |
| S18 | 2023 | Zhiling Zheng | 10.1021/jacs.3c12086 | 1,4 | AB |
| S19 | 2026 | M. Arjmandi | 10.1016/j.ccr.2025.217211 | 2,4 | AB |
| S20 | 2026 | Seyed Amir Ahghar | 10.1007/s11269-026-04790-1 | 2 | AB |
| S21 | 2025 | Bo Han | 10.1016/j.enconman.2025.120272 | 2,3 | MD (+SEEN-ONLY) |
| S22 | 2020 | Kasturi Nagesh Pai | 10.1021/acs.iecr.0c02339 | 3 | AB |
| S23 | 2022 | Kasturi Nagesh Pai | 10.1016/j.seppur.2022.120783 (abstract via chemRxiv 10.26434/chemrxiv-2021-26xgh) | 3 | AB |
| S24 | 2022 | Sai Gokul Subraveti | 10.1021/acs.iecr.1c04731 | 3 | AB |
| S25 | 2020 | Thomas D. Burns | 10.1021/acs.est.9b07407 | 3,4 | AB |
| S26 | 2020 | Kasturi Nagesh Pai | 10.1016/j.seppur.2020.116651 | 3 | AB |
| S27 | 2023 | Arvind Rajendran | 10.1021/acs.accounts.3c00335 | 3 | AB |
| S28 | 2022 | Sun Hye Kim | 10.1016/j.cherd.2022.10.002 | 3 | MD |
| S29 | 2026 | Beatrice Ceccanti | arXiv:2601.09491 | 3 | AB |
| S30 | 2025 | Mattia Galanti | 10.3390/pr13092824 | 3 | AB |
| S31 | 2025 | Zhiqiang Wu | 10.1016/j.gce.2024.08.004 | 3 | AB |
| S32 | 2025 | Abhijit Dhamanekar | arXiv:2502.02268 | 2,3 | AB |
| S33 | 2022 | Xiang Zhang | 10.1002/aic.17788 | 3 | AB |
| S34 | 2026 | M. Calvo-Schwarzwalder | arXiv:2607.17941 | 3 | AB |
| S35 | - | NIST/ARPA-E ISODB | adsorption.nist.gov/isodb/api/... (index, gases, materials, one isotherm) | 4 | DS |
| S36 | 2014 | Hiroyasu Furukawa | 10.1021/ja500330a | 4 | AB |
| S37 | 2023 | N. Scott Bobbitt | 10.1021/acs.jced.2c00583 | 4 | AB |
| S38 | 2022 | Daniele Ongari | 10.1021/acs.jced.1c00958 | 4 | AB |
| S39 | 2025 | Guobin Zhao | 10.1016/j.matt.2025.102140 (abstract via chemRxiv v2) | 3,4 | AB |
| S40 | 2025 | Shiue-Min Shih (Crossref) | 10.1021/jacs.5c10686 | 4 | AB |
| S41 | 2022 | Ha L. Nguyen | 10.1021/acscentsci.2c00398 | 5 | AB |
| S42 | 2023 | Chao Sun | 10.1002/anie.202217103 | 5 | AB |
| S43 | 2023 | Lars Grunenberg | 10.1021/jacs.3c02572 | 5 | AB |
| S44 | 2025 | Ha L. Nguyen | 10.1021/acscentsci.4c01878 | 4,5 | AB |
| S45 | 2023 | Ha L. Nguyen | 10.1002/adma.202300018 | 5 | AB |
| S46 | 2024 | Fuxiang Wen | 10.1002/cssc.202400049 | 5 | AB |
| S47 | 2025 | Yuan He | 10.1039/d5ew00643k | 5 | AB (short) |
| S48 | 2025 | Zhenhui Chen | 10.1016/j.cej.2025.171055 | 5 | MD (+SEEN-ONLY) |
| S49 | 2022 | Li L (Europe PMC) | 10.3390/nano12010159 | 4 | AB |
| S50 | 2020 | Cho KH (Europe PMC) | 10.1038/s41467-020-18968-7 | 2,4 | FT |
| S51 | 2015 | Martijn F. de Lange | 10.1021/acs.chemrev.5b00059 | 2,4 | MD |
| S52 | 2024 | Bo Zhang | 10.1002/adfm.202304788 | 4,5 | AB |
| S53 | 2017 | Francis Meunier | 10.1126/science.aao0361 | 1 | AB |
| S54 | 2017 | Duc Thuan Bui | 10.1126/science.aao0791 | 1 | AB |
| S55 | - | Dubai RDI grant page | dubairdi.ae/grant-initiatives-the-ai-enabled-digital-twin-... | 2 | WEB |
| S56 | 2023 | Andrey A. Bezrukov | 10.1016/j.xcrp.2023.101252 ; Zenodo 10.5281/zenodo.6631711 ; github.com/AndreyBezrukov/Water_Sorption_Kinetics | 1,2,4 | AB+DS |
| S57 | 2024 | Nathan P. Ortiz | 10.1016/j.xcrp.2024.102115 | 1,2 | AB |
| S58 | 2023 | John Young | 10.1016/j.cej.2022.141035 | 3 | AB |
| S59 | 2024 | Charithea Charalambous | 10.1038/s41586-024-07683-8 | 3 | AB |
| S60 | 2026 | Seong Ho Hong | 10.1016/j.applthermaleng.2026.132018 | 2 | MD |
| S61 | 2023 | Rasikh Tariq | 10.1016/j.icheatmasstransfer.2022.106538 | 2 | AB |
| S62 | 2025 | CoRE MOF 2024 dataset (Zhao, Guobin ...) | Zenodo 10.5281/zenodo.15055758 | 4 | DS |

SEEN-ONLY leads NOT fetched (not evidence): Parmar & Hindoliya 2011, Uckan et al. 2014, Jani et al. 2016 (ANN desiccant
wheels); Santana et al. 2022 (PINN ion-exchange column, 10.3390/chemengineering6020021); Priyadarshi et al. 2022 (ANFIS
desiccant HX); Keshavarz et al. 2026, multi-objective ML for AWH MOFs (10.1016/j.mtcomm.2026.115393); Ding et al. 2025,
multi-cycle AWH sorbent utilisation (10.1016/j.eesus.2025.100025, record only, no abstract); "AI-driven discovery of MOFs
for AWH", J. Mater. Chem. A 2026 (d6ta01583b); ACS Sustain. Chem. Eng. 2023 ML water-harvesting MOF screening
(10.1021/acssuschemeng.3c01233); Leperi/Snurr/You ANN-PSA surrogate (not located); Farooq-group and M.M.F. Hasan-group
PSA-ML papers (not located by my queries - absence here is NOT evidence of absence).

## Per-question findings

### Q1. MOF/COF harvesters with reusable data
- Only THREE items with machine-readable, licensed data were found:
  1. Bezrukov et al. 2023 (S56): raw DVS uptake-vs-time data and isotherms for what appear to be 7 MOFs + Syloid, including
     cycling experiments. 607 MB, CC-BY-4.0, with analysis code. Lab scale (DVS), not a field device.
  2. Song et al. 2023 (S07): a Zenodo Origin project (.opju, 2.3 MB, CC-BY-4.0) behind a passive MOF-303 harvester tested in
     Death Valley and Berkeley (114-285 g/kg/day, one cycle/day).
  3. Almassad et al. 2022 (S09): a Nature Communications Source Data xlsx (20.9 MB; the article is CC BY) for an adaptive
     MOF-801 device (3.5 L/kg/day claimed, 17-32% RH, multi-day, real weather). File contents not opened.
- Everything else is figures-only or "on request": Fathieh 2018 (S03), Kim 2018 (S08), Hanikel 2019 (S04; still the best
  same-geometry 4-sorbent kinetic comparison), Hanikel 2021 (S05; Zenodo holds DFT CIFs only), Cho 2020 LTJ kinetics (S50).
- Several headline yields come from MODELS, not measurements: Kim 2017 (disputed in two Science comments, S53/S54),
  Kim 2018 (the yield was computed because 3 g of sorbent was too little to measure, S08) and Ortiz & Rao 2024 ("can be
  achieved", S57). Only measured quantities should serve as ground truth.
- COF-432 (S06) and the later COFs are materials papers. No COF device with deposited data was found (see Q5).
- Suitability as ground truth for a device-level model: Song 2023 and Almassad 2022 are the only device traces with
  deposited files, and each covers a single material (MOF-303 and MOF-801). Cross-material ground truth exists only at the
  DVS/TGA level: Bezrukov 2023 is open, and Hanikel 2019 is available only as figures.

### Q2. Models and digital twins of sorption harvesters / AHPs / desiccant wheels
- Physics state of the art:
  - MIT/Wang-group heat-and-mass-transfer models (S08, S10, S11).
  - LDF with one k per sorbent, driven by reanalysis weather, for 12 sorbents (Ying 2025, S14).
  - An isotherm-shape-based cycling model with bed-surface diffusion limitation, for 8 sorbents (Bezrukov 2023, S56).
  - A Rao-group AHX model for cycle truncation and fin thickness (S57).
  - Monoexponential (LDF-like) kinetic fits (S04).
  S11, S56, S57 and S58 agree on two points: kinetics and transport, not only the isotherm, set productivity; and cycling
  at partial loading is optimal.
- ML work falls into four groups:
  - material-property ML for AWH MOFs (S18, S19, S49);
  - single-device static regression: GPR on one desiccant AWH rig (S20), an ANN of one desiccant cooling plant called a
    "digital twin" (S61), and ANN surrogates of one desiccant wheel trained on transient simulations (S15);
  - AutoML fault diagnosis of a 3-bed adsorption chiller (S16);
  - physics digital twins for fault detection or energy optimisation: S60 (MOF desiccant dehumidifier) and S17 (multi-bed
    adsorption system), both known from their titles only.
  Real-time control on a MOF harvester exists, but it is rule-based (S09).
- Not found: any neural-ODE, neural-operator, PINN or RL model of a sorption WATER HARVESTER; any learned harvester model
  that takes the sorbent as an input; any learned model validated on held-out sorbents. One funded project (S55) targets an
  "AI digital twin" of a MOF AWH system; its page lists no outputs.

### Q3. ML for adsorption columns / PSA / TSA and transfer to unseen materials
- Transfer to unseen materials HAS been done:
  - MAPLE (S22) takes Langmuir parameters and adsorbent properties as inputs and predicts CSS purity, recovery, energy and
    productivity.
  - Pai et al. 2022 (S23) fed MAPLE measured isotherms of 13X and LiX that were not in its training data. They then
    validated the surrogate's optimum on a two-column rig (mean errors 3%, 5% and 9%).
  - Burns 2020 (S25) ran 1632 MOFs through a validated VSA simulator and added an ML classifier.
  - Zhang 2022 (S33), Young 2023 (S58), PrISMa 2024 (S59) and the CoRE MOF 2024 TSA screening (S39/S62) are material-to-
    process pipelines for gas separation.
- Dynamic and neural-operator work:
  - PANACHE PINNs predict full spatiotemporal column states and assemble cycles without retraining (S24).
  - DeepONets generalise over INITIAL CONDITIONS for TVSA steps (S29).
  - Hybrid PINNs have been applied to DAC (S30).
  - One PINN uses "transfer learning" across time windows (S31).
  According to their abstracts, none of these vary the material at test time.
- The gap our paper can still claim is therefore narrower than "first surrogate that predicts unseen sorbents". It is:
  (a) transient, trajectory-level prediction (not CSS KPIs), (b) for held-out REAL sorbents, (c) with stepped or hysteretic
  WATER isotherms, (d) under temperature-swing or ambient-driven harvesting, (e) scored against measured kinetics.
  I found no paper that does (a) and (b) together, even for gas PSA. The search was keyword- and API-based, and two
  relevant items were not opened: Kim/Boukouvala 2022 (S28) and the Han & Chakraborty 2025 review (S21). Both must be read
  before this claim goes into a manuscript.

### Q4. Water-isotherm and kinetic data for real MOFs/COFs
- NIST ISODB (S35):
  - 1,221 pure-water isotherms, 557 adsorbent records, 275 DOIs.
  - About 95% digitised from figures; mostly at 298 K.
  - Missing: MOF-303, Co2Cl2(BTDD), SAPO-34, COF-432 and all the Yaghi harvester papers. Furukawa 2014 is only partly
    included (12 curves).
  - Usage rights are unclear (the site says "All rights reserved" and credits SpringerMaterials for some data).
- CoRE MOF 2024 (S39, S62): GEMC-SIMULATED water isotherms for the computation-ready set (water.zip), CC-BY-4.0, plus
  structures and ML stability labels. The largest open water set on real structures, but simulated.
- Other simulated sources: MOFX-DB (S37) has no water. Shih & Lin 2025 (S40) simulated water in >200 MOFs (deposit not
  verified). Li et al. 2022 (S49) ran GCMC for H2O/N2/O2 in 6013 CoRE MOFs and 137,953 hMOFs (equilibrium only).
- Kinetic (uptake-rate) data: Bezrukov 2023 (S56) is the only open RAW multi-material water-kinetics set found.
  Figure-only kinetic sets:
  - Hanikel 2019: 4 sorbents, same geometry;
  - Cho 2020: G-LTJ on KMF-1 vs MOF-303 and Co-CUK-1;
  - Sun 2023: COF rates.
- Shortlists for building a real-material set:
  - the Zhang et al. 2024 review (~40 MOFs + 1 COF, S52);
  - Furukawa 2014 (23 materials, S36);
  - LAMOF-1..10 + MOF-303 (S18) and the MTV-MOF-303 series (S05) as same-topology families.

### Q5. COF water harvesting
- Materials:
  - COF-432 (S06): S-shaped isotherm, no hysteresis, 300 cycles.
  - Hydrazine-hydrazide COF (S41): step below 18% RH, 0.45 g/g.
  - DHTA-Pa (S42): 0.48 g/g at 30% RH; 0.72 L/kg/h adsorption, 2.58 L/kg/h desorption; >90% released in 20 min at 313 K.
  - Nitrone-linked COFs (S43): condensation at ~20% lower RH.
  - HCOF-2, HCOF-3 and COF-309 (S44).
  - Anionic TpPa-2SO3Li (S48): numbers SEEN-ONLY.
- Modelling and ML: the only item found is a structure-derived "hydrophilicity index" that predicts the isotherm step for
  both COFs and MOFs (S44).
- COFs are still at the materials stage. The reviews (S45, S46, S47) and the Zhang 2024 shortlist, which includes one COF
  (S52), confirm this. ISODB has ~30 COF water isotherms, but not COF-432 or COF-309.
- No COF device field test with deposited data was found, and no COF kinetics dataset.
- A COF case in our paper would therefore have to be one of: (i) isotherm-only (from ISODB or digitised) inside a simulated
  study; (ii) digitised DHTA-Pa or COF-432 curves. Otherwise the title should drop "COF".

### Q6. Nobel Prize 2025
- VERIFIED from the fetched press release (S01): Susumu Kitagawa, Richard Robson and Omar M. Yaghi, "for the development
  of metal-organic frameworks". The release names water harvesting from desert air as an application.

## Datasets we could actually use

| Name | What it contains | Licence / access | URL |
|---|---|---|---|
| Bezrukov et al. 2023 data (S56) | Raw DVS exports (time, uptake, RH target/actual, T): isotherms and uptake/cycling kinetics for ~7 MOFs (ROS-037/039/040, MOF-303, Al-fumarate, MIL-160, CAU-10-H, per code strings) + Syloid; 607 MB zip | CC-BY-4.0 (Zenodo). The GitHub code has NO licence: reuse the ideas, do not redistribute the code | https://doi.org/10.5281/zenodo.6631711 ; https://github.com/AndreyBezrukov/Water_Sorption_Kinetics |
| Song et al. 2023 data (S07) | Origin project behind the Death Valley / Berkeley passive MOF-303 harvester figures (field T, RH, production; contents unverified) | CC-BY-4.0 (Zenodo); .opju needs OriginLab or a converter | https://doi.org/10.5281/zenodo.7990951 |
| Almassad et al. 2022 Source Data (S09) | xlsx (20.9 MB) behind the figures of an adaptive MOF-801 harvester (RH/dew point vs time, cycles, production; contents unverified) | Article CC BY 4.0; Nature ESM | https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-022-32642-0/MediaObjects/41467_2022_32642_MOESM3_ESM.xlsx |
| NIST/ARPA-E ISODB (S35) | 1,221 pure-water isotherms, 557 adsorbents, JSON via API; mostly 298 K; mostly digitised | Public API; the site says "All rights reserved", so cite and re-download rather than redistribute | https://adsorption.nist.gov/isodb/api/isotherms.json |
| CoRE MOF 2024 (S62) | Structures and properties for 2,664 CR MOFs; GEMC-simulated water isotherms (water.zip); water-stability probability; TSA data for 35 MOFs | CC-BY-4.0 (Zenodo) | https://doi.org/10.5281/zenodo.15055758 |
| Hanikel et al. 2019 figures (S04) | TGA uptake/desorption vs time for MOF-303, Al-fumarate, SAPO-34 and 13X in the same 3 mm bed; Table 1 rates | Open-access article (PMC6813556); data must be digitised | https://europepmc.org/article/PMC/PMC6813556 |
| Ying et al. 2025 code (S14) | MATLAB process models (passive/active continuous SAWH); 3 hydrogel isotherm files; LDF k values in SI Table S4 | Apache-2.0 | https://github.com/SAWH-Ying/Continuous-SAWH-pre |
| Hanikel et al. 2021 Zenodo (S05) | DFT CIFs of MOF-303 / MOF-333 at different water loadings (structures only) | CC-BY-4.0 | https://doi.org/10.5281/zenodo.5294977 |
| Furukawa 2014 via ISODB (S36/S35) | 12 water isotherms at 298 K for 11 Zr MOFs and others | as ISODB | ISODB files 10.1021Ja500330a.Isotherm* |

Not usable for water: MOFX-DB (S37 has no water adsorbate).

## Gaps (each tied to evidence)
1. No learned dynamic model of a sorption water harvester takes the sorbent as an input. ML in AWH is either
   material-property prediction (S18, S19, S49) or single-device static regression (S20). Sorption "digital twins" are
   single-plant ANNs (S61), physics replicas (S32; S60 by title) or fault classifiers (S16).
2. Material transfer is established only for gas PSA, at the level of cyclic-steady-state KPIs (S22, S23, S25). Neural
   dynamic surrogates generalise over initial conditions or time windows, not materials (S24, S29, S31).
3. There is one open, raw, multi-material WATER kinetics dataset (S56). The others are figures or "on request" (S04, S08,
   S50, S42).
4. Physics models reduce kinetics to one LDF constant per sorbent (S14) or a monoexponential fit (S04). S56, however,
   reports that uptake is limited by diffusion to the bed surface, so the kinetic "material property" is partly a property
   of the bed and setup. A cross-material learner must control for sample mass, bed depth and flow, or it will learn the
   setup instead of the material.
5. Headline device yields are often model projections (S02/S53/S54, S08, S57). The community has no benchmark of measured,
   multi-material device dynamics.
6. COFs have no kinetics dataset, no device data and no dynamic model (S41-S48). The only tool is an isotherm-step
   descriptor (S44).

## Closest prior work for "A digital twin of a MOF water harvester: learning cycle dynamics across materials"
1. Bezrukov et al. 2023 (S56): one physics model, parameterised by each sorbent's isotherm, simulates water-harvesting
   cycling for 8 sorbents, and the raw kinetics are open. This is the baseline to beat and the dataset to use. A reviewer
   will ask why ML is needed if this model already transfers across materials.
2. Pai et al. 2020 / 2022, MAPLE (S22, S23), plus the Rajendran Account (S27): a surrogate that takes the material as an
   input, with experimentally validated predictions for adsorbents not in training. Must be cited as prior material
   transfer.
3. Ying et al. 2025 (S14): an LDF + isotherm process model across 12 sorbents under global weather, with open MATLAB code.
4. Subraveti et al. 2022 PANACHE (S24) and Ceccanti et al. 2026 DeepONet (S29): neural surrogates of cyclic adsorption
   dynamics, each for a single material.
5. Almassad et al. 2022 (S09): real-time adaptive cycle control of a MOF harvester (rule-based), with source data.
6. Hanikel et al. 2019 (S04): same-geometry multi-sorbent water kinetics. Song et al. 2023 (S07): deposited device data.
7. Uses of "digital twin" in sorption systems: Tariq 2023 (S61), Hong 2026 (S60), Chen 2022 (S17), Dhamanekar 2025 (S32),
   plus the funded competitor S55.

Defensible novelty, assuming the unread S21 and S28 do not already cover it:
- a learned model of TRANSIENT water-sorption cycle dynamics, conditioned on sorbent descriptors (isotherm plus
  kinetic/transport properties);
- scored by leave-one-material-out on MEASURED kinetics (S56) and checked against device traces (S07, S09);
- compared head-to-head with an isotherm+LDF physics baseline of the S56/S14 kind.

## Risks
1. Novelty challenge from the adsorption-process community: MAPLE-style transfer already exists (S22/S23). Claims must be
   scoped to dynamics + water + held-out real materials.
2. Baseline risk: an isotherm + LDF model (or the S56 bed-diffusion model) may already predict held-out sorbents well. If
   ML does not beat it, the contribution shrinks to a benchmark, which may still be publishable if framed honestly.
3. Small n: ~8 sorbents with raw kinetics (S56) plus 4 that could be digitised (S04). Leave-one-material-out on 8-12
   materials gives wide error bars, so report per-material results, not only means.
4. Confounding: uptake is limited by diffusion to the bed surface (S56) and depends on bed geometry (S04 fixed a 3 mm bed
   with porosity 0.7). Differences in setup between papers can masquerade as material differences. Do not pool kinetics
   across labs without covariates.
5. Label quality: exclude model-projected yields (S02, S08, S57) from ground truth.
6. Format and licence friction: the .opju file (S07) needs Origin; ISODB rights are unclear; the S56 code has no licence.
7. Terminology: "digital twin" implies live data assimilation with a physical asset, and our work (an offline surrogate)
   could be criticised on that basis. A funded project (S55) and a 2026 MOF-desiccant digital-twin paper (S60) already
   use the term.
8. The COF claim cannot be supported with measured dynamics (Q5).
9. Unverified items:
   - S17, S21, S28, S51 and S60 are known by title only;
   - the contents of the S07 .opju and the S09 xlsx have not been opened;
   - the 7-MOF list in S56 is inferred from code strings;
   - S40's first author differs between records (Crossref "Shiue-Min Shih", OpenAlex "Shang-Chuan Shih").
10. Search coverage: API and keyword searches only. Paywalled full texts and non-English literature were not covered. My
    queries did not locate the Farooq and M.M.F. Hasan PSA-ML papers or the Leperi/Snurr/You ANN-PSA work.
