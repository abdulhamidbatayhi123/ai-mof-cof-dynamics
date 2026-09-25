# Literature: MOF/COF water harvesters, device models / digital twins, ML for adsorption processes, water-isotherm data

Compiled 2026-09-25 by a literature-research agent. Rule 8: a source counts only if FETCHED (abstract,
Crossref/OpenAlex record or full text actually opened). SEEN-ONLY entries are leads, not evidence.
Authors are written exactly as the fetched record shows them (initials kept as initials).
"Crossref record" means only metadata (title/authors/year/journal) was confirmed, not content, unless an
abstract is stated.

Status: IN PROGRESS (appended source by source; synthesis sections at the end).

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
  abstract states 2.8 L water per kg MOF per day at 20% RH. (Later commentary questioned this figure as a
  projection; see S-notes below if fetched.)
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

### S07. Song, Zheng, Alawadhi, Yaghi 2023, Nature Water - Death Valley harvester (Q1) - FETCHED (Crossref METADATA ONLY)
- DOI: 10.1038/s44221-023-00103-7. Authors (Crossref): Woochul Song, Zhiling Zheng, Ali H. Alawadhi, Omar M. Yaghi. 2023.
- Title only confirmed: MOF water harvester produces water from Death Valley desert air in ambient sunlight. No abstract in
  Crossref/OpenAlex; nature.com redirected to login. Content NOT verified -> treat numbers as unverified.

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

