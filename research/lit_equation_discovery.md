# Literature: data-driven equation discovery for adsorption / breakthrough, and identifiability

Compiled 2026-09-25 by a literature-research agent. Rule 8: a source counts only if FETCHED (abstract or
full text actually opened). SEEN-ONLY entries are leads, not evidence. Authors are written exactly as the
fetched record shows them (initials kept as initials).

Status: COMPLETE 2026-09-25 (source log S1-S65, then synthesis sections (a)-(e) at the end).

## Source log (appended as fetched)

### S1. Santana et al. 2023, Chem. Eng. Sci. -- UDE + SINDy/SR for sorption kinetics in a fixed bed  [FETCHED]
- ids: DOI 10.1016/j.ces.2023.119223 (Crossref record opened); arXiv:2303.13555 (abs v1-v3 and HTML v3 full text opened)
- authors as shown (Crossref): Vinicius V. Santana, Erbet Costa, Carine M. Rebello, Ana Mafalda Ribeiro, Christopher Rackauckas, Idelfonso B.R. Nogueira (arXiv shows "Chris Rackauckas"). Year 2023.
- title: "Efficient hybrid modeling and sorption model discovery for non-linear advection-diffusion-sorption systems: A systematic scientific machine learning approach"
- what the fetched text says: a neural net replaces the solid-fluid mass-transfer term inside the fixed-bed PDE
  (universal differential equation, adjoint sensitivities); then SINDy (Lasso/ADMM, polynomial library up to 6th order,
  BIC to choose sparsity) and genetic-programming SR (SymbolicRegression.jl) are applied to the learned term.
  Ground truths: LDF 0.22(q*-q), Vermeulen, "improved LDF"; isotherms Langmuir and Sips. Synthetic outlet breakthrough
  curves with 5 % Gaussian noise. For LDF the recovered form is p1 + p2 q + p3 q* with p2 ~ -0.22, p3 ~ 0.22.
  The isotherm is treated as KNOWN AND FIXED (q* supplied); only the kinetic term is discovered. The text concedes that
  recovering the right interaction term from noisy observations is "not trivial", and for Vermeulen the uptake rate is
  underestimated despite a good breakthrough fit.
- relevance: the single closest prior work. It does discovery of the LDF law from breakthrough data, but at one kinetic
  rate, one noise level, with exact q*. It does NOT map success vs Damkohler, does not test measured/misspecified
  isotherms, and gives no identifiability analysis. The candidate's "exact-q* works, measured-q* fails" result is a
  direct extension/contradiction test of this paper's setting.
- S1 addendum (second fetch of arXiv HTML v3, parameters as given): L = 2.0 dm, interstitial v = 0.51 dm/min,
  porosity 0.5, Pe = 21.0, c_in 5.5 mg/L, 110 min training window sampled at 0.5 min^-1, OUTLET DATA ONLY, one noise
  level (5 %), the 0.22 LDF factor was NOT varied. OUR computation (not stated in S1): if k = 0.22 min^-1 and
  Da = k L / v, then Da = 0.22 x 2.0 / 0.51 ~ 0.86 -- i.e. S1 sits in the KINETICALLY CONTROLLED regime, below the
  candidate's 3.8-689 range. Under that definition S1's success is consistent with, not contrary to, the candidate's
  map; the candidate should recompute S1's Da with its own Da definition (capacity factor included or not) and plot S1
  as an external point on the map.

### S2. Praditia et al. 2022, Water Resour. Res. -- FINN learns sorption isotherm / retardation factor  [FETCHED]
- id: DOI 10.1029/2022WR033149 (Crossref record with abstract opened)
- authors as shown: Timothy Praditia, Matthias Karlbauer, Sebastian Otte, Sergey Oladyshkin, Martin V. Butz, Wolfgang Nowak. 2022 (issued 29 Nov 2022), WRR 58(12).
- fetched abstract says: finite-volume neural network learns stencils, parameters and closure relations; on
  diffusion-sorption it identifies sorption isotherms (via the retardation factor) without restricting to a parametric
  isotherm, and with UQ beats a calibrated PDE model on lab experiments.
- relevance: analogous reactive-transport discovery, but the learned closure is the EQUILIBRIUM isotherm (local
  equilibrium assumed, no kinetic rate); no symbolic extraction and no regime map. Shows the equilibrium side is
  learnable from breakthrough data -- the complement of the candidate's kinetic question.

### S3. Scheurer et al. 2026, Front. Water -- confidence intervals for FINN sorption learning  [FETCHED]
- id: DOI 10.3389/frwa.2026.1813791 (publisher full-text page opened)
- authors as shown: Stefania Scheurer, Riccardo Frenner, Tim Brünnette, Sergey Oladyshkin, Wolfgang Nowak. Published 7 May 2026.
- fetched text says: data-driven bootstrapping + PI3NN gives confidence intervals on the learned retardation factor
  R(c) ~45x faster than BNN-MCMC; the bootstrap exposes multimodal solutions -- two local optima of the
  physics-constrained learning problem with similar predicted concentrations.
- relevance: direct evidence of PRACTICAL non-identifiability of a learned sorption closure from breakthrough-type data
  (different closures, same observables). Supports the candidate's framing; competitor for UQ tooling (bootstrap
  ensembles), but not a Damkohler-regime map and not about kinetics.

### S4. Haghpanah & Shade 2023, Ind. Eng. Chem. Res. -- SR fits adsorption isotherms  [FETCHED (abstract via OpenAlex; Crossref metadata)]
- id: DOI 10.1021/acs.iecr.3c02900 (Crossref record opened: no abstract; OpenAlex record opened: abstract reconstructed). ACS page returned 403.
- authors as shown: Reza Haghpanah, Danny Shade. 2023 (issued 12 Dec 2023), IECR 62(51) 22141-22148. Funded by Dow.
- fetched abstract says: symbolic regression empirically generates isotherm equations for difficult datasets,
  including water vapour and CO2 on flexible adsorbents at multiple temperatures, without prior physical knowledge.
- relevance: SR for EQUILIBRIUM (isotherm) only, incl. water on flexible/stepped adsorbents -- relevant to the MOF
  step-isotherm question (item 4). Not kinetics, not breakthrough. SR tool not visible in the fetched abstract.

### S5. Shao et al. 2026, arXiv -- SR expression for CO2 uptake in hypothetical MOFs  [FETCHED (abstract)]
- id: arXiv:2608.14990 (abs page opened), submitted 15 Aug 2026
- authors as shown: Yimin Shao, Shengluo Ma, Shenghong Ju, Yijun Shi, Wei Li
- fetched abstract says: ML + SHAP on 1,000 simulated hMOF samples picks 5 structural descriptors; SR gives Q = aA
  with A a dimensionless group of four features; >70 % accuracy on 62,448 structures.
- relevance: MOF SR, but structure-property (screening) regression, not dynamics/kinetics. Not a competitor to the
  candidate; shows MOF-SR work is in the descriptor->uptake space, not the rate-law space.

### S6. Sharlin & Josephson 2024/2026, arXiv -- LLM-driven SR rediscovers Langmuir / dual-site Langmuir  [FETCHED (abstract)]
- id: arXiv:2410.17448 (abs page opened; v1 22 Oct 2024, v3 16 Apr 2026)
- authors as shown: Samiha Sharlin, Tyler R. Josephson
- fetched abstract says: GPT-4/GPT-4o propose expressions, external Python tools fit/evaluate; rediscovers Langmuir
  and dual-site Langmuir; admits it "does not outperform established SR programs" on harder targets.
- relevance: isotherm (equilibrium) SR only; confirms PySR-class GP SR is still the stronger baseline.

### S7. Sircar & Hufton 2000, Adsorption -- "Why does the LDF model for adsorption kinetics work?"  [METADATA FETCHED; CONTENT SEEN-ONLY]
- id: DOI 10.1023/A:1008965317983 (Crossref, OpenAlex, Semantic Scholar records opened; none carry the abstract; Springer page redirects to login)
- authors as shown: Crossref "S. Sircar, J.R. Hufton"; OpenAlex "Shivaji Sircar, Jeffrey R. Hufton". Adsorption 6(2):137-147, June 2000.
- SEEN-ONLY (search snippet, not evidence): pore/particle-level kinetic detail is lost through repeated averaging,
  which is why LDF works for column data. If confirmed from full text, this is the classical statement that column
  data cannot discriminate kinetic mechanisms -- a structural prior for the candidate's non-identifiability claim.

### S8. Knox et al. 2016, Ind. Eng. Chem. Res. -- "Limitations of breakthrough curve analysis in fixed-bed adsorption"  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1021/acs.iecr.6b00516 (OpenAlex record opened, abstract reconstructed)
- authors as shown: James C. Knox, Armin D. Ebner, M. Douglas LeVan, R. F. Coker, James A. Ritter. 2016, IECR 55(16) 4734-4748.
- fetched abstract says: compares a-priori axial-dispersion correlations with fitting both dispersion and LDF mass
  transfer from breakthrough data (1-D axially dispersed plug flow, Danckwerts BCs), CO2 and H2O on zeolite 5A; finds
  potential for erroneous extraction of the dispersion coefficient and/or the LDF coefficient under non-plug flow;
  reliable extraction needs internal bed measurements confirming constant-pattern behaviour near the exit.
- relevance: classical adsorption-engineering evidence that the LDF k is NOT reliably recoverable from outlet
  breakthrough alone (confounded with dispersion). Water on zeolite included. A referee will cite this for the
  "k is hard to identify" half of the candidate's claim -- the candidate must go beyond it (regime map + discovery).

### S9. Calvo-Schwarzwalder et al. 2026, arXiv -- equilibrium models for dynamic adsorption; PFO-Sips column  [FETCHED (abstract)]
- id: arXiv:2607.17941 (abs page opened), submitted 20 Jul 2026
- authors as shown: M. Calvo-Schwarzwalder, A. Valverde, A. Cuesta López, A. Cabrera-Codony, U. Thorat, T.G. Myers
- fetched abstract says: travelling-wave analysis of a PFO-kinetics + Sips column model gives an abrupt breakthrough
  unlike the pure Sips model; against experiments PFO does worse and has internal inconsistencies; they call PFO
  inadequate for column dynamics. No Damkohler/identifiability discussion in the abstract.
- relevance: shows the kinetic-law choice (PFO vs equilibrium) in columns is actively disputed in 2026; a candidate
  whose library includes PFO/PSO/LDF should cite this. Not equation discovery.

### S10. Loman & Baker 2025, arXiv -- functional vs parametric identifiability of UDEs (chemical reaction networks)  [FETCHED (abstract)]
- id: arXiv:2510.14140 (abs page opened), submitted 15 Oct 2025
- authors as shown: Torkel E Loman, Ruth E Baker
- fetched abstract says: splits UDE identifiability into parametric (mechanistic part) and functional (the NN-learned
  function); studies how NN count and constraints affect both; turning a mechanistic model into a UDE has little
  effect on the mechanistic parameters' identifiability.
- relevance: the closest METHODOLOGICAL framing to "can the learned kinetic term be identified" -- the candidate's
  learned-rate-law question is a functional-identifiability question. Not adsorption, no regime map.

### S11. Gallo, Anselmi & Lazzari 2026, arXiv -- attractor geometry sets identifiability limits of SINDy and PySR  [FETCHED (abstract)]
- id: arXiv:2607.18490 (abs page opened), submitted 20 Jul 2026
- authors as shown: Matteo Gallo, Fabio Anselmi, Paolo Lazzari
- fetched abstract says: on Lorenz-84, the smallest eigenvalue of the invariant-measure moment matrix (how fully the
  trajectory spans the library's function space) sets an identifiability ceiling for BOTH SINDy and PySR; noise enters
  SINDy's regression bottleneck linearly and PySR's discrimination channel superlinearly; introduces "Soft F1".
- relevance: HIGH for the "discoverability" framing. This is a general (non-adsorption) theory that library
  conditioning determined by where the data live bounds recovery. Near local equilibrium the data sit on q ~ q*(c),
  i.e. a thin slow manifold -> small lambda_min for {q, q*} columns -> the candidate's failure is an instance of this.
  The candidate should cite it and could compute lambda_min (or the condition number of the library Gram matrix)
  per Damkohler as a mechanistic predictor of its map. Also a referee may argue the candidate's result is
  "just" this theory specialised -- the candidate must show adsorption-specific content (Da scaling, measured-q* bias).

### S12. Klishin, Bakarji, Kutz & Manohar 2024, arXiv -- statistical mechanics of system identification  [FETCHED (abstract)]
- id: arXiv:2403.01723 (abs page opened; v1 4 Mar 2024, revised 4 Feb 2025)
- authors as shown: Andrei A. Klishin, Joseph Bakarji, J. Nathan Kutz, Krithika Manohar
- fetched abstract says: sparse equation discovery treated as a two-level Bayesian / statistical-mechanics problem
  with closed-form posteriors; identifies sparsity- and noise-induced phase transitions separating successful from
  failed identification.
- relevance: prior art for "success/failure phase diagram vs noise" in sparse regression. The candidate's map adds a
  PHYSICAL axis (Damkohler) to the noise axis; it must acknowledge this noise-axis phase-transition literature.

### S13. Fung 2026, ACM Trans. AI for Science -- ODR-BINDy for error-in-variables / stiffness in SINDy  [FETCHED (Crossref abstract)]
- id: DOI 10.1145/3831701 (Crossref record with abstract opened; doi.org redirects to dl.acm.org)
- authors as shown: Lloyd Fung. Issued 18 Jul 2026.
- fetched abstract says: standard SINDy regression assumes noise only in the derivative target, not in the states;
  proposes orthogonal distance regression + Bayesian model selection (ODR-BINDy) with the model equation as a soft
  constraint; recovers Lorenz63 with up to 30 % noise; beats existing variants on sparse noisy data.
- relevance: the candidate's measured-q* failure is an ERRORS-IN-VARIABLES problem in the regressor q* (isotherm
  error ~ size of driving force). ODR-BINDy is a strong competitor configuration that explicitly targets this.

### S14. Fasel, Kutz, Brunton & Brunton 2022, Proc. R. Soc. A -- Ensemble-SINDy  [FETCHED (abstract)]
- ids: arXiv:2111.10992 (abs opened), DOI 10.1098/rspa.2021.0904 (shown on abs page)
- authors as shown: Urban Fasel, J. Nathan Kutz, Bingni W. Brunton, Steven L. Brunton. arXiv Nov 2021; journal 2022.
- fetched abstract says: bagging over data (and library) gives inclusion probabilities for candidate terms, enabling UQ
  and probabilistic forecasts; handles >2x the noise of prior PDE-discovery reports; same scaling as SINDy.
- relevance: STANDARD strong baseline; inclusion probability is the natural per-(Da, noise) success metric for the map.

### S15. Delgado-Cano, Kracht, Fasel & Herrmann 2025, arXiv -- SINDy on slow manifolds  [FETCHED (abstract)]
- id: arXiv:2507.00747 (abs page opened), submitted 1 Jul 2025
- authors as shown: Diemen Delgado-Cano, Erick Kracht, Urban Fasel, Benjamin Herrmann
- fetched abstract says: for slow-fast systems, the SINDy regression "becomes simultaneously computationally intractable
  and ill-conditioned"; fix = first identify the slow manifold as an algebraic equation, then learn slow dynamics with
  a manifold-informed library.
- relevance: HIGH. High-Da adsorption is a slow-fast system whose slow manifold is q = q*(c). This paper says SINDy
  is ill-conditioned there and that the recoverable object is the MANIFOLD (i.e. the isotherm) plus slow dynamics --
  exactly the candidate's finding that equilibrium is recoverable and k is not. Must be cited.

### S16. Muhammed, Manias, Goussis & Hatzikirou 2025, PLOS Comput. Biol. -- SINDy + CSP for multiscale systems  [FETCHED (abstract)]
- id: DOI 10.1371/journal.pcbi.1013193 (PLOS article page opened), published 6 Nov 2025
- authors as shown: Ismaila Muhammed, Dimitris M. Manias, Dimitris A. Goussis, Haralampos Hatzikirou
- fetched abstract says: SINDy fails to find one global model when trajectories cross time-scale regimes; computational
  singular perturbation (Jacobian eigenstructure via NN) partitions data into regime-homogeneous subsets where SINDy
  recovers valid reduced models.
- relevance: regime-dependent discoverability in biology; conceptually the same move as a Damkohler map. A regime
  classifier by timescale separation is a competitor idea (e.g. partition breakthrough data by local Da).

### Core method papers (all FETCHED abstract pages; cited as the methods a referee expects)
- S17. Brunton, Proctor & Kutz -- SINDy. arXiv:1509.03580 (abs opened, submitted 11 Sep 2015); DOI 10.1073/pnas.1517384113 (PNAS 2016, shown on abs page). Authors as shown: Steven L. Brunton, Joshua L. Proctor, J. Nathan Kutz. Sparse regression over a candidate library; assumes few active terms. [FETCHED]
- S18. Rudy, Brunton, Proctor & Kutz -- PDE-FIND. arXiv:1609.06401 (abs opened, submitted 21 Sep 2016). Authors as shown: Samuel H. Rudy, Steven L. Brunton, Joshua L. Proctor, J. Nathan Kutz. Sparse selection of nonlinear and partial-derivative terms, Pareto analysis; Eulerian and Lagrangian data. (Journal version Sci. Adv. 2017 not shown on the fetched page -- not verified here.) [FETCHED]
- S19. Messenger & Bortz -- Weak SINDy. arXiv:2005.04339 (abs opened; May 2020), DOI 10.1137/20M1343166 (shown). Authors as shown: Daniel A. Messenger, David M. Bortz. Replaces pointwise derivatives with test-function integrals; orders-of-magnitude better than SINDy under noise; coefficient error scales favourably with SNR. [FETCHED]
- S20. Reinbold, Gurevich & Grigoriev -- weak-form PDE discovery. arXiv:1911.03365 (abs opened), Phys. Rev. E 101, 010203 (2020) (shown). Authors as shown: Patrick A.K. Reinbold, Daniel R. Gurevich, Roman O. Grigoriev. Weak formulation avoids high-order derivatives of noisy data; handles latent (unmeasured) variables. [FETCHED] -- relevant: in a column only c(outlet,t) is measured, q is latent.
- S21. Kaheman, Kutz & Brunton -- SINDy-PI. arXiv:2004.02322 (abs opened; Apr/Sep 2020), DOI 10.1098/rspa.2020.0279 (shown). Authors as shown: Kadierdan Kaheman, J. Nathan Kutz, Steven L. Brunton. Implicit/rational dynamics; several orders of magnitude more noise-robust than implicit-SINDy; Belousov-Zhabotinsky. [FETCHED] -- relevant: Langmuir/Toth/cooperative isotherms enter the rate law as rational functions.
- S22. Bortz, Messenger & Dukic -- WENDy. arXiv:2302.13271 (abs opened; Feb-Apr 2023). Authors as shown: David M. Bortz, Daniel A. Messenger, Vanja Dukic. Weak-form parameter estimation, errors-in-variables + IRLS, no forward solver, faster and more accurate on stiff systems. [FETCHED] -- relevant: parameter-estimation (not discovery) competitor for k under noise.
- S23. Cranmer -- PySR. arXiv:2305.01582 (abs opened; 2 May 2023). Author as shown: Miles Cranmer. Multi-population evolutionary SR (evolve-simplify-optimize), Julia backend, EmpiricalBench. [FETCHED]
- S24. Udrescu & Tegmark -- AI Feynman. arXiv:1905.11481 (abs opened), Sci. Adv. 6:eaay2631 (2020) (shown). Authors as shown: Silviu-Marian Udrescu, Max Tegmark. NN-guided recursive SR exploiting symmetry/separability; 100/100 Feynman equations. [FETCHED]
- S25. Liu et al. -- KAN. arXiv:2404.19756 (abs opened; v1 30 Apr 2024, v5 9 Feb 2025; ICLR 2025 shown). Authors as shown: Ziming Liu, Yixuan Wang, Sachin Vaidya, Fabian Ruehle, James Halverson, Marin Soljačić, Thomas Y. Hou, Max Tegmark. Spline activations on edges; interpretability / symbolic extraction claimed. [FETCHED]

### S26. de Carvalho Servia et al. 2024, Digital Discovery -- ADoK-S / ADoK-W automated kinetic-rate-model discovery  [FETCHED (abstract)]
- ids: DOI 10.1039/d3dd00212h (OpenAlex record opened; RSC HTML returned 403); arXiv:2301.11356 (abs opened; Jan 2023, rev. Nov 2023)
- authors as shown (arXiv): Miguel Ángel de Carvalho Servia, Ilya Orson Sandoval, Klaus Hellgardt, King Kuok (Mimi) Hii, Dongda Zhang, Ehecatl Antonio del Rio Chanona. (OpenAlex lists the same six, order Hii before Hellgardt.) 2024.
- fetched abstract says: GP symbolic regression in a strong form (rates estimated from concentrations) and a weak form
  (integrated, no rate estimation), plus sequential parameter refinement, information-criterion model selection and
  model-based design of experiments; recovers catalytic rate laws from limited noisy data in three case studies.
- relevance: strongest chemical-engineering precedent for SR-based RATE-LAW discovery with information criteria and
  MBDoE. Batch catalytic kinetics, not columns; no regime map. The weak (integral) SR form is a competitor config.

### S27. de Carvalho Servia et al. 2025, arXiv -- PI-ADoK: constraint-guided SR for kinetic discovery  [FETCHED (abstract)]
- id: arXiv:2507.02730 (abs opened; 3 Jul 2025)
- authors as shown: Miguel Ángel de Carvalho Servia, Ilya Orson Sandoval, King Kuok (Mimi) Hii, Klaus Hellgardt, Dongda Zhang, Ehecatl Antonio del Rio Chanona
- fetched abstract says: physical constraints inside SR narrow the search space and cut experiments needed;
  Metropolis-Hastings propagates parameter uncertainty into credible prediction intervals.
- relevance: physics-constrained SR (e.g. enforce rate = 0 at q = q*, sign constraints) is a natural strong competitor
  for the candidate, directly attacking the "correct sign only 69 %" failure.

### S28. Shukla et al. 2025, J. Phys. Chem. Lett. -- CRNN discovers CO adsorption/desorption pathways  [METADATA FETCHED; CONTENT SEEN-ONLY]
- id: DOI 10.1021/acs.jpclett.5c00665 (Crossref record opened; the returned "abstract" was a generic paraphrase of the title -- treat as not read)
- authors as shown: Jay Shukla, Xiaohui Qu, Zubin Darbari, Marija Iloska, J. Anibal Boscoboinik, Qin Wu. Issued 1 Apr 2025.
- relevance (title-level only): chemical reaction neural network used to discover surface adsorption/desorption
  kinetics from transient spectroscopy -- analogous kinetic discovery, not column transport.

### Negative-search evidence (FETCHED search APIs)
- OpenAlex search "sparse identification nonlinear dynamics adsorption" (25 results, opened) returned NO paper applying
  SINDy to adsorption kinetics/columns; OpenAlex search "symbolic regression adsorption kinetics" (25 results, opened)
  returned only Santana et al. 2023 (S1) as an SR/SINDy study of adsorption kinetics. This supports -- but does not
  prove -- that equation discovery of adsorption RATE laws from column data is a thin literature (one main paper).

### S29. Katsoulas, Tirapelle, Sørensen & Mazzei 2023, J. Chromatogr. A -- apparent dispersion coefficient of the EDM, asymptotic analysis  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1016/j.chroma.2023.464345 (OpenAlex record opened, abstract reconstructed; UCL Discovery page returned 403)
- authors as shown: Konstantinos Katsoulas, Monica Tirapelle, Eva Sørensen, Luca Mazzei. 2023, J. Chromatogr. A 1708, 464345.
- fetched abstract says: the equilibrium dispersion model assumes local equilibrium and accounts for FINITE MASS-TRANSFER
  RATES only through an apparent dispersion coefficient; two competing expressions exist; an asymptotic derivation from
  the pore-diffusion model supports the less-used one, confirmed on simulated elution profiles.
- relevance: HIGH (structural identifiability). Near local equilibrium the column model collapses to the EDM in which
  k appears ONLY inside a lumped apparent dispersion together with axial dispersion. So from outlet data at one flow
  rate, k and D_L are confounded (only their combination is identifiable). This is the classical mechanism behind the
  candidate's high-Da failure and it predates ML. The candidate must cite it and state what is new beyond it.

### S30. Miyabe & Guiochon 2000, J. Chromatogr. A -- lumped mass-transfer coefficient by frontal analysis  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1016/s0021-9673(00)00537-9 (OpenAlex record opened; PubMed page gave only a cookie wall)
- authors as shown: Kanji Miyabe, Georges A. Guiochon. 2000, J. Chromatogr. A 890(2) 211-223.
- fetched abstract says: breakthrough (frontal) curves fitted with a solid-film LDF transport model give the lumped rate
  coefficient kf; kf varies linearly with concentration within a step; shock-layer theory predictions agree.
- relevance: counter-evidence the candidate must handle: in the constant-pattern / shock-layer regime (favourable
  isotherm), k IS estimable from the front width by parameter fitting when the isotherm is known and dispersion is
  small. So the claim cannot be "k is unidentifiable at high Da" tout court; it must be "k is not DISCOVERABLE by
  derivative-based regression on (q*-q) when q* is measured/misspecified", or be conditioned on dispersion/noise.

### S31. Felinger, Cavazzini & Dondi 2004, J. Chromatogr. A -- stochastic-dispersive vs lumped kinetic model equivalence  [FETCHED (abstract via OpenAlex; low detail)]
- id: DOI 10.1016/j.chroma.2004.05.081 (OpenAlex record opened; PubMed page cookie wall)
- authors as shown: Attila Felinger, Alberto Cavazzini, Francesco Dondi. 2004, J. Chromatogr. A 1043(2) 149-157.
- fetched abstract (paraphrase, reconstructed by the fetch tool at low fidelity): the microscopic stochastic-dispersive
  model and the macroscopic lumped kinetic model are equivalent when parameters are matched.
- relevance: model-equivalence = structural non-identifiability of mechanism from elution data.

### S32. Qamar, Bashir, Perveen & Seidel-Morgenstern 2019, J. Liq. Chromatogr. -- relations between kinetic parameters of column models  [METADATA FETCHED; CONTENT SEEN-ONLY]
- id: DOI 10.1080/10826076.2019.1570522 (Crossref record opened: no abstract; T&F page 403)
- authors as shown: Shamsul Qamar, Seemab Bashir, Sadia Perveen, Andreas Seidel-Morgenstern. 2019.
- SEEN-ONLY (search snippet): moment matching gives relations between kinetic parameters of different models, so
  simpler models can match the general rate model. Not counted as evidence.

### S33. Ward & Pini 2022, Adsorption -- integrated UQ + Sobol sensitivity of dynamic column breakthrough  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1007/s10450-022-00361-z (OpenAlex record opened, abstract reconstructed; Springer page redirects to login)
- authors as shown: Adam S. Ward, Ronny Pini. 2022, Adsorption 28(3-4) 161-183.
- fetched abstract says: CO2/He on activated carbon; 1-D column model fitted to breakthrough + internal temperature;
  Bayesian inference for parameter uncertainty, propagated (~±15 % on outlet concentration and temperature);
  Sobol analysis attributes ~70 % of output variability to the ISOTHERM parameters and their T-dependence.
- relevance: HIGH. Direct experimental-adsorption evidence that breakthrough outputs are dominated by equilibrium
  parameters, i.e. kinetic parameters carry little output variance -> weak practical identifiability of k. The
  Bayesian+Sobol workflow is the incumbent identifiability tool in adsorption engineering; the candidate's map should
  be benchmarked against (or computed with) it.

### S34. Hyun, Jung & Choi 2025, Sep. Purif. Technol. -- physics-aware Bayesian breakthrough framework  [METADATA FETCHED; CONTENT SEEN-ONLY]
- id: DOI 10.1016/j.seppur.2025.135612 (OpenAlex record opened; abstract null)
- authors as shown: Yesol Hyun, Heesoo Jung, Jung-Il Choi. 2025, SPT 381, 135612.
- SEEN-ONLY (search snippet): says inverse fitting of breakthrough data is intrinsically ill-posed; lumped
  mass-transfer coefficient trades off against an apparent catalytic rate; uses time-segmented global sensitivity.
  Not counted as evidence until the abstract/full text is read.

### S35. Taylor, Herman & Morales 2026, J. Contam. Hydrol. -- global sensitivity of sorption/degradation transport across Péclet-Damköhler regimes  [FETCHED (abstract via Semantic Scholar)]
- id: DOI 10.1016/j.jconhyd.2026.105043 (Semantic Scholar record with abstract opened; Crossref and OpenAlex records opened, no abstract; PubMed cookie wall)
- authors as shown: Crossref "W. Taylor, J.D. Herman, V.L. Morales"; OpenAlex "W. Taylor, J.D. Herman, Verónica L. Morales". 2026 (issued Nov 2026), vol. 283, 105043.
- fetched abstract says: global sensitivity analysis of 1-D saturated advection-dispersion-reaction simulations varying
  porosity, bulk density, dispersivity, decay rate, Kd and DESORPTION RATE; influence evaluated at early arrival, peak
  and late tailing, individually and with interactions, interpreted in Pe-Da regimes; sorption (equilibrium) consistently
  drives transport, decay dominates reaction-controlled cases, dispersion can dominate advection-dominated cases.
- relevance: HIGH -- the closest "regime map" prior art. It maps PARAMETER SENSITIVITY (not equation discovery)
  across Pe-Da for sorbing transport and finds equilibrium sorption dominates. A referee will cite it against a
  Da-regime identifiability map. The candidate differs by (i) asking whether the RATE LAW can be DISCOVERED (structure,
  sign, sparsity), not just whether a known parameter is sensitive, (ii) adsorption-column (nonlinear isotherm, MOF)
  setting, (iii) noise axis and measured-isotherm error. It does NOT pre-empt the discovery question.

### S36. Hansen & Vesselinov 2017, arXiv -- local equilibrium and retardation revisited  [FETCHED (abstract)]
- id: arXiv:1703.03087 (abs opened; 9 Mar 2017)
- authors as shown: Scott K. Hansen, Velimir V. Vesselinov
- fetched abstract says: classical local-equilibrium validity criteria really measure whether mass-transfer-driven
  dispersion is negligible relative to hydrodynamic dispersion; remobilisation rate, not LEA per se, controls validity
  of the retarded ADE.
- relevance: states in transport language that near equilibrium the kinetic effect appears only as extra dispersion,
  so it is distinguishable only when it is not swamped by hydrodynamic dispersion -> the identifiability of k depends
  on (Da, Pe) jointly, not Da alone. The candidate's map should include Pe (or show Pe is fixed and say so).

### S37. Valocchi 1985, Water Resour. Res. -- validity of the local equilibrium assumption  [FETCHED (Crossref abstract, low detail)]
- id: DOI 10.1029/wr021i006p00808 (Crossref record with abstract opened)
- author as shown: "Valocchi, Albert J." 1985, WRR 21(6) (808-820 per search snippet).
- fetched abstract (paraphrase): derives criteria comparing equilibrium and kinetic sorbing-transport models (temporal
  moments), showing velocity, dispersion and rate jointly decide whether local equilibrium holds.
- relevance: the classical origin of "LEA validity depends on a Damkohler-type ratio AND dispersion" -- i.e. the
  theoretical reason k becomes invisible at high Da. Must be cited as the pre-ML root of the identifiability map.


### S38. Delahunt & Kutz 2021, arXiv -- toolkit for SINDy in high-noise regimes  [FETCHED (abstract)]
- id: arXiv:2111.04870 (abs opened; v1 8 Nov 2021, v2 29 Dec 2021)
- authors as shown: Charles B. Delahunt, J. Nathan Kutz
- fetched abstract says: progressive culling of over-complete libraries; Lorenz recovered with median coefficient
  error 1-3 % at 50 % noise up to 23-25 % at 300 % noise; also a technique for MODEL NON-UNIQUENESS that uses linear
  dependencies among library functionals to map discovered models to the form closest to ground truth.
- relevance: near equilibrium q ~ q*(c) makes the {q, q*} columns nearly linearly dependent -- precisely the
  non-uniqueness this toolkit addresses. The candidate's "q term selected 100 % but sign right 69 %, no
  sparsification" is a textbook collinearity symptom; this toolkit is a fair strong-SINDy competitor.

### S39. Abu El-Maaty et al. 2024, Energy Convers. Manag. X -- water adsorption kinetics in MOF-303 (LDF)  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1016/j.ecmx.2024.100694 (OpenAlex record opened, abstract reconstructed)
- authors as shown: Ahmed E. Abu El-Maaty, Mahmoud A. Abdalla, Mohamed Essalhi, Mahmoud M. Abdelnaby, Morsi M. Mahmoud, Mohamed A. Habib, Mohamed Antar, Rached Ben-Mansour. 2024.
- fetched abstract says: equilibrium and uptake-rate measurements of water on MOF-303 across RH and T; LDF used to
  extract diffusion coefficients; ~8x faster uptake than silica gel; an isotherm inflection at 10-15 % relative
  pressure coincides with marked reductions in the specific diffusion rate.
- relevance: MOF water kinetics are fitted with LDF by hand; the LDF constant is NOT constant across the step
  (concentration-dependent k). No equation discovery. This is the MOF-specific gap: a discovered k(q) or
  isotherm-slope-dependent rate law near the step is untested.

### S40. Altamirano et al. 2025, Adsorption -- dual-site Langmuir + association-theory model for Al-fumarate/water  [METADATA FETCHED; CONTENT SEEN-ONLY]
- id: DOI 10.1007/s10450-025-00649-w (OpenAlex and Semantic Scholar records opened; abstract elided by publisher)
- authors as shown: OpenAlex "Amín Altamirano, Cécile Daniel, David Farrusseng, Francis E. Meunier, Orhan Talu"; Semantic Scholar "A. Altamirano, Cécile Daniel, David Farrusseng, F. Meunier, Orhan Talu". 2025, Adsorption 31(7).
- SEEN-ONLY (snippet): Langmuir on strong sites + cooperative water clustering (association theory) for S-shaped
  water isotherms. Hand-derived physical model -- a target an isotherm-SR study should rediscover.

### S41. Coyle et al. 2026, arXiv -- MOF water harvesters in the AI era (review)  [FETCHED (abstract)]
- id: arXiv:2605.29179 (abs opened; 27 May 2026, rev. 15 Jun 2026)
- authors as shown: Reid A. Coyle, Shyam Chand Pal, Peter Walther, Saeun Park, Bin Feng, Zhiling Zheng
- fetched abstract says: AI/LLM/data-mining for MOF water-harvester design, predictive synthesis, inverse design.
  The abstract does not mention equation discovery, SR or kinetic-model learning.
- relevance: a 2026 review of AI for MOF water harvesting whose abstract is silent on data-driven kinetics -- weak
  evidence the MOF water-kinetics discovery niche is open.

### S42. Frandsen et al. 2025, AIChE J. -- systematic screening of 10 NN-hybrid adsorption models in chromatography  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1002/aic.70045 (OpenAlex record opened; Wiley page 403)
- authors as shown: Jesper R. Frandsen, Vinicius V. Santana, Peter Jul–Rasmussen, Idelfonso B. R. Nogueira, Jakob Kjøbsted Huusom, Krist V. Gernaey, Jens Abildskov. 2025, AIChE J 71(12).
- fetched abstract says: ten hybrid architectures in which NNs replace different parts of the adsorption formulation
  inside mechanistic chromatography transport; binary non-reactive and four-component reactive case studies; most
  hybrids match the validated mechanistic model, few beat it.
- relevance: the same group as S1, extending to WHERE to put the NN (isotherm vs kinetics vs both). A referee will
  cite S1+S42 together as "hybrid/UDE discovery of adsorption terms in columns is established". Abstract does not
  mention symbolic extraction, identifiability or a regime map.

### S43. Prabhu, Kosir, Kothare & Rangarajan 2025, Ind. Eng. Chem. Res. -- DF-SINDy (derivative-free, domain-informed)  [FETCHED (PMC full text page)]
- id: DOI 10.1021/acs.iecr.4c02981; PMC11803628 (opened)
- authors as shown: Siddharth Prabhu, Nick Kosir, Mayuresh V Kothare, Srinivas Rangarajan. 2025.
- fetched text says: integral (not derivative) SINDy with mass-balance / chemistry constraints; Gaussian noise sd 0.1
  and 0.2; chemistry-informed variant recovers the true terms without spurious ones where plain SINDy fails; stiff
  reactions faster than the sampling frequency caused parameter-estimation errors for ALL methods.
- relevance: HIGH. (a) Integral + constrained SINDy is a strongest-configuration competitor for the candidate;
  (b) its stated failure mode (stiffness vs sampling) is the kinetic analogue of the high-Da failure -- the candidate
  should report Da relative to the sampling interval, not only Da.

### S44. Ito, Kuwatani, Oyanagi & Omori 2021, Entropy -- sparse modelling + SMC for heterogeneous reactions with hidden states  [FETCHED (PMC page)]
- id: DOI 10.3390/e23070824; PMC8303197 (opened)
- authors as shown: Masaki Ito, Tatsu Kuwatani, Ryosuke Oyanagi, Toshiaki Omori. 2021.
- fetched text says: adaptive Lasso + sequential Monte Carlo jointly select reaction terms and estimate hidden solid
  states from observations of only the dissolved intermediate.
- relevance: methodological template for the column case where the solid loading q is HIDDEN and only outlet c is
  observed -- a discovery-with-latent-state configuration the candidate should consider or justify skipping.

### S45. Huang, Zhou & Yong 2021, J. Comput. Phys. -- discovering multiscale (stiff) reactions under mass action  [FETCHED (abstract)]
- ids: arXiv:2101.06589 (abs opened); DOI 10.1016/j.jcp.2021.110743 (shown)
- authors as shown: Juntao Huang, Yizhou Zhou, Wen-An Yong. 2021.
- fetched abstract says: with multiple timescales, conventional optimisers get stuck in local minima; a
  partial-parameters-freezing technique exploiting integer stoichiometry recovers Michaelis-Menten, H2 oxidation and
  reduced GRI-3.0.
- relevance: another documented timescale-separation failure of equation discovery.

### S46. Katsoulas, Galvanin, Mazzei & Sorensen 2026, Ind. Eng. Chem. Res. -- diagnostic procedure for identifying isotherm models in LC  [FETCHED (PMC page)]
- id: DOI 10.1021/acs.iecr.5c03704; PMC12828779 (opened)
- authors as shown: Katsoulas, K.; Galvanin, F.; Mazzei, L.; Sorensen, E. 2026.
- fetched text says: a Lagrange-multiplier test (are parameters independent of the state?) plus goodness-of-fit
  iteratively replaces constant parameters by state-dependent functions to build the isotherm structure; in one case
  the structurally correct quadratic isotherm gave poor ML estimates (flat objective, local optima).
- relevance: a STATISTICAL-TEST route to structure discovery (not SINDy/SR) from chromatographic data, with explicit
  identifiability caveats. Competitor/alternative for "is k constant or k(q)?" -- the LM test is directly usable to
  ask whether the LDF coefficient must be state-dependent (cf. MOF-303, S39).

### S47. Bakarji & Tartakovsky 2021, J. Comput. Phys. -- data-driven discovery of coarse-grained equations  [FETCHED (abstract)]
- ids: arXiv:2002.00790 (abs opened; Jan-Jul 2020); DOI 10.1016/j.jcp.2021.110219 (shown)
- authors as shown: Joseph Bakarji, Daniel M. Tartakovsky
- fetched abstract says: sparse regression learns PDF equations of a nonlinear PDE with random inputs, either directly
  from a full dictionary or in a constrained mode that learns only the unknown closure.
- relevance: "constrained equation learning of only the closure" = the right framing for learning only the uptake term
  inside a known column PDE (the candidate's configuration). Reactive-transport-adjacent (advection-reaction).

### S48. Slote, Fish & Bollt 2026, arXiv -- KANDy: KANs + sparse regression for dynamical-system discovery  [FETCHED (abstract)]
- id: arXiv:2602.20413 (abs opened; Feb-Mar 2026). Authors as shown: Kevin Slote, Jeremie Fish, Erik Bollt.
- fetched abstract says: combines KANs with sparse regression for equation discovery in discrete/continuous systems
  and chaotic PDEs. No noise or failure analysis in the abstract.
- relevance: the current KAN-based discovery configuration; a KAN competitor should be KANDy-style (KAN + sparse
  regression), not raw pykan auto_symbolic.

### S49. Spotorno, Leal Filho & Frohlich 2026, arXiv -- stability of KANs in hard-constrained physics-informed discovery  [FETCHED (abstract)]
- id: arXiv:2602.09988 (abs opened; Feb-Mar 2026). Authors as shown: Enzo Nicolas Spotorno, Josafat Leal Filho, Antonio Augusto Medeiros Frohlich.
- fetched abstract says: KANs show severe hyperparameter fragility, instability when deeper, and consistent failure on
  multiplicative terms (Van der Pol); small KANs are competitive only on univariate polynomial residuals (Duffing);
  MLPs generally outperform KANs.
- relevance: the LDF term k(q*(c) - q) is a bivariate/multiplicative structure when k or q* depend on state; this is
  evidence that KAN symbolic extraction is a WEAK competitor for it -- include KAN but do not make it the headline.

### S50. Koenig & Deng 2025/2026, arXiv -- KA-CRNN for pressure-dependent kinetic rate laws  [FETCHED (abstract)]
- id: arXiv:2511.07686 (abs opened; Nov 2025, rev. May 2026). Authors as shown: Benjamin C. Koenig, Sili Deng.
- fetched abstract says: chemical reaction NNs with Kolmogorov-Arnold activations learn kinetic parameters as functions
  of third-body concentration, keeping Arrhenius/mass-action structure; 2.88x lower MSE than interpolative approaches.
- relevance: shows the productive KAN use is INSIDE a structured (mass-action) model to learn a 1-D dependency --
  analogous to learning k(q) or k(T) inside a fixed LDF structure.

### S51. Cornelio et al. 2021/2023, arXiv -- AI Descartes (data + theory, derivable discovery)  [FETCHED (abstract)]
- id: arXiv:2109.01634 (abs opened; Sep 2021 - Jan 2023 v4). (Nature Commun. 2023 version not shown on page -- not verified.)
- authors as shown: Cristina Cornelio, Sanjeeb Dash, Vernon Austel, Tyler Josephson, Joao Goncalves, Kenneth Clarkson, Nimrod Megiddo, Bachir El Khadir, Lior Horesh
- fetched abstract says: SR + formal logical reasoning from background theory; demonstrated on Kepler's third law,
  relativistic time dilation and Langmuir's theory of adsorption; laws recoverable from few data points.
- relevance: isotherm (equilibrium) SR benchmark; theory-constrained SR as a strong-configuration idea.

### S52. Fox, Tran, Nacion, Sharlin & Josephson 2023, arXiv -- background knowledge in SR via computer algebra  [FETCHED (abstract)]
- id: arXiv:2301.11919 (abs opened; Jan-May 2023)
- authors as shown: Charles Fox, Neil Tran, Nikki Nacion, Samiha Sharlin, Tyler R. Josephson
- fetched abstract says: symbolic constraints (background knowledge) as soft constraints improve SR search and
  interpretability at higher compute cost; rediscovering adsorption equations from experimental historical datasets.
- relevance: thermodynamic-constraint SR for ISOTHERMS (Josephson group line: S6, S51, S52). Equilibrium only.

### Negative-search evidence 2 (FETCHED arXiv API)
- arXiv API query all:adsorption AND (SINDy OR "symbolic regression" OR "equation discovery" OR "sparse identification"),
  40 max, returned 13 hits (opened). Only arXiv:2303.13555 (S1) addresses adsorption KINETICS in a column; the rest are
  isotherm SR (S6, S51, S52), MOF descriptor SR (S5), catalysis adsorption energies, or irrelevant.

### S53. Stanhope, Rubin & Swigon 2014, SIAM J. Appl. Dyn. Syst. -- identifiability of linear-in-parameters systems from a single trajectory  [FETCHED (Crossref abstract, verbatim check)]
- id: DOI 10.1137/130937913 (Crossref record opened; abstract text read directly)
- authors as shown: S. Stanhope, J. E. Rubin, D. Swigon. 2014.
- fetched abstract says: necessary and sufficient identifiability conditions for linear and linear-in-parameters
  systems (i.e. exactly the SINDy model class) from one error-free trajectory; one result depends only on the
  trajectory's geometric structure; with discrete data, estimation sensitivity depends on a condition number tied to
  the data's "spatial confinement".
- relevance: HIGH -- the theoretical anchor for the candidate. A breakthrough run at high Da is a single trajectory
  confined near the slow manifold q = q*(c); spatial confinement -> ill-conditioning -> k not identifiable. Pairs with
  S11 (lambda_min of the moment matrix) and S15 (ill-conditioning on slow manifolds). The candidate should state its
  map as a quantitative instance of this condition, and could measure the confinement directly.

### S54. Messenger & Bortz 2021 -- Weak SINDy for PDEs  [FETCHED (abstract)]
- id: arXiv:2007.02848 (abs opened; Jul-Dec 2020). Authors as shown: Daniel A. Messenger, David M. Bortz.
- fetched abstract says: machine-precision recovery from noise-free data, robust PDE identification at large noise;
  links robustness to test-function spectra; adaptive threshold; exploits scale invariance for poorly scaled data.
- relevance: WSINDy-PDE is the strongest-configuration SINDy for the column PDE (c,q fields) when interior data exist;
  "poorly scaled" data (q ~ 10^3 x c in MOF columns) is explicitly handled.

### S55. Bertsimas & Gurnee 2022/2023 -- MIOSR: SINDy by mixed-integer optimisation  [FETCHED (abstract)]
- id: arXiv:2206.00176 (abs opened; 1 Jun 2022). Authors as shown: Dimitris Bertsimas, Wes Gurnee.
- fetched abstract says: L0-constrained SINDy solved to provable optimality in seconds; better sample efficiency,
  noise robustness and constraint flexibility than heuristic sparse regression.
- relevance: exact-L0 selection removes "the optimiser failed" as an explanation for non-sparsification; a
  must-include competitor (with sign constraints) before claiming the failure is identifiability, not optimisation.

### S56. Kaptanoglu, Zhang, Nicolaou, Fasel & Brunton 2023 -- benchmarking SINDy on low-dimensional chaos  [FETCHED (abstract)]
- id: arXiv:2302.10787 (abs opened; Feb 2023). (Nonlinear Dyn. 111(14) 2023 per search snippet -- not verified on fetched page.)
- authors as shown: Alan A. Kaptanoglu, Lanyue Zhang, Zachary G. Nicolaou, Urban Fasel, Steven L. Brunton
- fetched abstract says: four SINDy optimisers on the dysts chaotic-system database; original STLSQ and a mixed-integer
  algorithm perform strongly; weak form substantially better; performance shows NO significant dependence on chaos,
  SCALE SEPARATION, nonlinearity or syntactic complexity.
- relevance: COUNTER-EVIDENCE / risk. On attractor-filling chaotic data, scale separation does not predict SINDy
  success. The candidate must explain why Da matters for breakthrough data: transient single trajectories confined to
  the slow manifold (S53, S11), not attractor-filling data. Without that argument a referee can cite S56 against it.

### S57. Nogueira, Santana, Ribeiro & Rodrigues 2022, Can. J. Chem. Eng. -- UODE for multicomponent fixed-bed adsorption  [FETCHED (Crossref abstract)]
- id: DOI 10.1002/cjce.24495 (Crossref record opened)
- authors as shown: Idelfonso B. R. Nogueira, Vinicius V. Santana, Ana M. Ribeiro, Alírio E. Rodrigues. Issued 10 Jul 2022, CJChE 100(9) 2279-2290.
- fetched abstract says: universal ODE (NN + physics) for multicomponent fixed-bed adsorption identified from
  EXPERIMENTAL data; needs few data points; describes competitive adsorption better than Langmuir.
- relevance: precursor of S1 on real data. With S1 and S42 this group owns "UDE for adsorption columns". None of the
  three (as fetched) maps discoverability vs Da or noise.

### S58. Jessop, Alsubeihi, Moseley & Rajagopalan 2026, arXiv -- differentiable hybrid modelling of chemical transport from experiments  [FETCHED (abstract)]
- id: arXiv:2609.04011 (abs opened; 3 Sep 2026). Authors as shown: Arthur Jessop, Mohammed Alsubeihi, Ben Moseley, Ashwin Kumar Rajagopalan.
- fetched abstract says: JAX finite-volume solver + NN components learn constitutive laws and initial conditions from
  experimental data (population-balance framing); differentiable for process optimisation. No symbolic extraction or
  identifiability in the abstract.
- relevance: very recent (Sep 2026) differentiable-hybrid competitor from an adsorption-process group; watch it --
  a follow-up applying it to adsorption columns would sit close to the candidate.

### S59/S60. Metadata-only (abstract not available on fetched records) -- NOT evidence
- Emami-Meibodi 2023, Chem. Eng. Sci. 282, DOI 10.1016/j.ces.2023.119343, "A generalized dimensionless form of the
  break-through curve for adsorption processes" (OpenAlex opened, abstract null). Potentially relevant to which
  dimensionless group(s) are identifiable from a breakthrough curve; read before citing.
- Adegunju, Amalraj, Holland, Nicholson, Ebner & Ritter 2023/2024, Adsorption 30(1) 57-77, DOI 10.1007/s10450-023-00434-7,
  "Assessment of the new kinetically limited linear driving force model..." (OpenAlex opened, abstract null). A newer
  rate law (KLLDF) that a discovery library should be able to distinguish from LDF; read before citing.

### Negative-search evidence 3 (WebSearch only -- SEEN-ONLY, weak)
- Searches for SINDy/SR applied to PSA/TSA cyclic processes returned only POD reduced-order PSA models and generic
  SINDy papers; no SINDy/SR-for-PSA paper was found. Not proof of absence.

### S61. Subraveti, Li, Prasad & Rajendran 2022, J. Chromatogr. A -- PANACHE learns nonlinear chromatography without an isotherm  [FETCHED (abstract via OpenAlex)]
- id: DOI 10.1016/j.chroma.2022.463037 (OpenAlex record opened, abstract reconstructed)
- authors as shown: Sai Gokul Subraveti, Zukui Li, Vinay Prasad, Arvind Rajendran. 2022.
- fetched abstract says: physics-based NNs (conservation laws in the loss) simulate binary column dynamics without an
  explicit isotherm (mixed Langmuir; Tröger's base on Chiralpak AD with inflection isotherms); relative L2 ~1e-2;
  the models can INFER ISOTHERMS from dynamic separation data.
- relevance: again the equilibrium closure is inferable from column dynamics; complements S2 (FINN). Neither targets
  the kinetic coefficient -- consistent with the candidate's asymmetry (equilibrium recoverable, kinetics not).

### S62. Tang et al. 2023, J. Chromatogr. A -- PINNs for the lumped kinetic model  [METADATA FETCHED; CONTENT NOT SEEN]
- id: DOI 10.1016/j.chroma.2023.464346 (OpenAlex opened; abstract null -- the fetch tool's "inverse problem" gloss is
  not from the abstract and is disregarded). Authors as shown: Si-Yuan Tang, Yun-Hao Yuan, Yu-Cheng Chen, Shan-Jing Yao, Ying Wang, Dong-Qiang Lin.

### S63. Krishnapriyan, Gholami, Zhe, Kirby & Mahoney 2021, NeurIPS -- failure modes of PINNs  [FETCHED (abstract)]
- id: arXiv:2109.01050 (abs opened; Sep-Nov 2021). Authors as shown: Aditi S. Krishnapriyan, Amir Gholami, Shandian Zhe, Robert M. Kirby, Michael W. Mahoney.
- fetched abstract says: PINNs fail on convection/reaction/diffusion problems as the coefficients grow; cause is
  optimisation ill-conditioning from the soft PDE penalty, not expressivity; curriculum and seq2seq training give
  1-2 orders lower error.
- relevance: precedent for "SciML success/failure mapped against a dimensionless coefficient" (reaction/convection
  strength ~ Da, Pe). A PINN-inverse competitor for k will itself degrade at high Da for OPTIMISATION reasons -- the
  candidate must separate optimisation failure from information (identifiability) failure, e.g. by showing the
  Fisher information / profile likelihood also collapses.

### S64. Raue et al. 2009, Bioinformatics -- profile likelihood for structural and practical identifiability  [FETCHED (Crossref abstract)]
- id: DOI 10.1093/bioinformatics/btp358 (Crossref record opened)
- authors as shown: A. Raue, C. Kreutz, T. Maiwald, J. Bachmann, M. Schilling, U. Klingmüller, J. Timmer. Issued 8 Jun 2009, Bioinformatics 25(15) 1923-1929.
- fetched abstract says: profile likelihood detects structural non-identifiability (functionally related parameters)
  and practical non-identifiability (limited data), yields confidence intervals, supports experimental planning and
  model reduction.
- relevance: THE standard tool for the candidate's k-vs-(D_L, isotherm) question; the map should show the profile of
  k flattening as Da rises. (Outside the 2016-2026 window, but it is the method reference.)

### S65. Hirsh, Barajas-Solano & Kutz 2021/2022 -- UQ-SINDy with sparsifying priors  [FETCHED (abstract)]
- id: arXiv:2107.02107 (abs opened; 5 Jul 2021). Authors as shown: Seth M. Hirsh, David A. Barajas-Solano, J. Nathan Kutz.
- fetched abstract says: spike-and-slab and regularised-horseshoe priors with MCMC give coefficient uncertainty AND
  posterior inclusion probability per candidate term; tested on Lotka-Volterra, oscillators, lynx-hare data.
- relevance: posterior inclusion probability of the (q*-q) term, and posterior of its coefficient sign, is a
  principled "discoverability" metric per (Da, noise) cell -- stronger than a frequency over random seeds.


---------------------------------------------------------------------------------------------------------------

# SYNTHESIS

## (a) Table of FETCHED sources

Evidence only. SEEN-ONLY or metadata-only items are left out (log S7, S28, S32, S34, S40, S59, S60, S62).
"Fetched" means the abstract or full text was opened (arXiv abs/HTML, Crossref/OpenAlex/Semantic Scholar abstract,
PMC or publisher page). Rows marked (low) had only a thin, tool-reconstructed abstract.

| Log | id (opened) | authors as shown | year | venue | one-line finding |
|---|---|---|---|---|---|
| S1 | DOI 10.1016/j.ces.2023.119223; arXiv:2303.13555 | Vinicius V. Santana, Erbet Costa, Carine M. Rebello, Ana Mafalda Ribeiro, Christopher Rackauckas, Idelfonso B.R. Nogueira | 2023 | Chem. Eng. Sci. | UDE + SINDy/GP-SR recover LDF (p2 ~ -0.22, p3 ~ 0.22) from 5 %-noise OUTLET breakthrough; isotherm given; one k, one noise level; Da ~0.9 by our calculation |
| S2 | DOI 10.1029/2022WR033149 | Timothy Praditia, Matthias Karlbauer, Sebastian Otte, Sergey Oladyshkin, Martin V. Butz, Wolfgang Nowak | 2022 | Water Resour. Res. | FINN learns the sorption isotherm (retardation factor) from diffusion-sorption data |
| S3 | DOI 10.3389/frwa.2026.1813791 | Stefania Scheurer, Riccardo Frenner, Tim Brünnette, Sergey Oladyshkin, Wolfgang Nowak | 2026 | Front. Water | bootstrap CIs expose two local optima of the learned sorption law with similar predictions |
| S4 | DOI 10.1021/acs.iecr.3c02900 | Reza Haghpanah, Danny Shade | 2023 | Ind. Eng. Chem. Res. | SR fits isotherms incl. water and CO2 on flexible adsorbents |
| S5 | arXiv:2608.14990 | Yimin Shao, Shengluo Ma, Shenghong Ju, Yijun Shi, Wei Li | 2026 | arXiv | SR descriptor-to-CO2-uptake formula for hypothetical MOFs |
| S6 | arXiv:2410.17448 | Samiha Sharlin, Tyler R. Josephson | 2024 (v3 2026) | arXiv | LLM-guided SR rediscovers Langmuir / dual-site Langmuir; below GP-SR on hard targets |
| S8 | DOI 10.1021/acs.iecr.6b00516 | James C. Knox, Armin D. Ebner, M. Douglas LeVan, R. F. Coker, James A. Ritter | 2016 | Ind. Eng. Chem. Res. | LDF k and dispersion can be wrongly extracted from outlet breakthrough; interior data needed |
| S9 | arXiv:2607.17941 | M. Calvo-Schwarzwalder, A. Valverde, A. Cuesta López, A. Cabrera-Codony, U. Thorat, T.G. Myers | 2026 | arXiv | PFO kinetics inconsistent in columns; worse than equilibrium Sips against experiment |
| S10 | arXiv:2510.14140 | Torkel E Loman, Ruth E Baker | 2025 | arXiv | functional vs parametric identifiability for UDEs |
| S11 | arXiv:2607.18490 | Matteo Gallo, Fabio Anselmi, Paolo Lazzari | 2026 | arXiv | smallest eigenvalue of the data moment matrix caps SINDy and PySR recovery |
| S12 | arXiv:2403.01723 | Andrei A. Klishin, Joseph Bakarji, J. Nathan Kutz, Krithika Manohar | 2024 | arXiv | sparsity- and noise-induced phase transitions in sparse identification |
| S13 | DOI 10.1145/3831701 | Lloyd Fung | 2026 | ACM Trans. AI Sci. | ODR-BINDy handles errors-in-variables and stiffness; Lorenz at 30 % noise |
| S14 | arXiv:2111.10992; DOI 10.1098/rspa.2021.0904 | Urban Fasel, J. Nathan Kutz, Bingni W. Brunton, Steven L. Brunton | 2022 | Proc. R. Soc. A | E-SINDy bagging gives term inclusion probabilities |
| S15 | arXiv:2507.00747 | Diemen Delgado-Cano, Erick Kracht, Urban Fasel, Benjamin Herrmann | 2025 | arXiv | SINDy intractable and ill-conditioned on slow-fast systems; learn the slow manifold first |
| S16 | DOI 10.1371/journal.pcbi.1013193 | Ismaila Muhammed, Dimitris M. Manias, Dimitris A. Goussis, Haralampos Hatzikirou | 2025 | PLOS Comput. Biol. | SINDy fails across timescale regimes; CSP partitions data into discoverable subsets |
| S17 | arXiv:1509.03580; DOI 10.1073/pnas.1517384113 | Steven L. Brunton, Joshua L. Proctor, J. Nathan Kutz | 2016 | PNAS | SINDy |
| S18 | arXiv:1609.06401 | Samuel H. Rudy, Steven L. Brunton, Joshua L. Proctor, J. Nathan Kutz | 2016 | arXiv (journal not verified) | PDE-FIND |
| S19 | arXiv:2005.04339; DOI 10.1137/20M1343166 | Daniel A. Messenger, David M. Bortz | 2020-21 | SIAM (DOI shown) | Weak SINDy; orders-of-magnitude noise gain |
| S20 | arXiv:1911.03365 | Patrick A.K. Reinbold, Daniel R. Gurevich, Roman O. Grigoriev | 2020 | Phys. Rev. E | weak-form PDE discovery with noise and latent variables |
| S21 | arXiv:2004.02322; DOI 10.1098/rspa.2020.0279 | Kadierdan Kaheman, J. Nathan Kutz, Steven L. Brunton | 2020 | Proc. R. Soc. A | SINDy-PI for implicit/rational dynamics |
| S22 | arXiv:2302.13271 | David M. Bortz, Daniel A. Messenger, Vanja Dukic | 2023 | arXiv | WENDy: weak-form errors-in-variables parameter estimation |
| S23 | arXiv:2305.01582 | Miles Cranmer | 2023 | arXiv | PySR / SymbolicRegression.jl |
| S24 | arXiv:1905.11481 | Silviu-Marian Udrescu, Max Tegmark | 2020 | Sci. Adv. | AI Feynman |
| S25 | arXiv:2404.19756 | Ziming Liu, Yixuan Wang, Sachin Vaidya, Fabian Ruehle, James Halverson, Marin Soljačić, Thomas Y. Hou, Max Tegmark | 2024-25 | ICLR 2025 | KAN with symbolic extraction |
| S26 | DOI 10.1039/d3dd00212h; arXiv:2301.11356 | Miguel Ángel de Carvalho Servia, Ilya Orson Sandoval, Klaus Hellgardt, King Kuok (Mimi) Hii, Dongda Zhang, Ehecatl Antonio del Rio Chanona | 2024 | Digital Discovery | strong/weak GP-SR + information criteria + MBDoE for rate-law discovery |
| S27 | arXiv:2507.02730 | Miguel Ángel de Carvalho Servia, Ilya Orson Sandoval, King Kuok (Mimi) Hii, Klaus Hellgardt, Dongda Zhang, Ehecatl Antonio del Rio Chanona | 2025 | arXiv | physics-constrained SR + Metropolis-Hastings UQ for kinetics |
| S29 | DOI 10.1016/j.chroma.2023.464345 | Konstantinos Katsoulas, Monica Tirapelle, Eva Sørensen, Luca Mazzei | 2023 | J. Chromatogr. A | near local equilibrium, finite mass transfer enters only through an apparent dispersion coefficient |
| S30 | DOI 10.1016/s0021-9673(00)00537-9 | Kanji Miyabe, Georges A. Guiochon | 2000 | J. Chromatogr. A | kf extracted from frontal breakthrough, consistent with shock-layer theory |
| S31 (low) | DOI 10.1016/j.chroma.2004.05.081 | Attila Felinger, Alberto Cavazzini, Francesco Dondi | 2004 | J. Chromatogr. A | stochastic-dispersive and lumped kinetic models are equivalent |
| S33 | DOI 10.1007/s10450-022-00361-z | Adam S. Ward, Ronny Pini | 2022 | Adsorption | Bayesian + Sobol: ~70 % of breakthrough output variance comes from isotherm parameters |
| S35 | DOI 10.1016/j.jconhyd.2026.105043 | W. Taylor, J.D. Herman, V.L. Morales | 2026 | J. Contam. Hydrol. | global sensitivity across Pe-Da: sorption equilibrium dominates breakthrough |
| S36 | arXiv:1703.03087 | Scott K. Hansen, Velimir V. Vesselinov | 2017 | arXiv | LEA criteria really test whether mass-transfer dispersion is negligible vs hydrodynamic dispersion |
| S37 (low) | DOI 10.1029/wr021i006p00808 | Valocchi, Albert J. | 1985 | Water Resour. Res. | LEA validity criteria from temporal moments (velocity, dispersion, rate) |
| S38 | arXiv:2111.04870 | Charles B. Delahunt, J. Nathan Kutz | 2021 | arXiv | SINDy toolkit for 50-300 % noise; resolves non-uniqueness from linearly dependent functionals |
| S39 | DOI 10.1016/j.ecmx.2024.100694 | Ahmed E. Abu El-Maaty, Mahmoud A. Abdalla, Mohamed Essalhi, Mahmoud M. Abdelnaby, Morsi M. Mahmoud, Mohamed A. Habib, Mohamed Antar, Rached Ben-Mansour | 2024 | Energy Convers. Manag. X | LDF fitted to MOF-303 water uptake; diffusion rate drops at the isotherm step |
| S41 | arXiv:2605.29179 | Reid A. Coyle, Shyam Chand Pal, Peter Walther, Saeun Park, Bin Feng, Zhiling Zheng | 2026 | arXiv | AI-for-MOF-water review; abstract silent on kinetics discovery |
| S42 | DOI 10.1002/aic.70045 | Jesper R. Frandsen, Vinicius V. Santana, Peter Jul–Rasmussen, Idelfonso B. R. Nogueira, Jakob Kjøbsted Huusom, Krist V. Gernaey, Jens Abildskov | 2025 | AIChE J. | 10 NN-hybrid adsorption structures screened in chromatography |
| S43 | DOI 10.1021/acs.iecr.4c02981 (PMC11803628) | Siddharth Prabhu, Nick Kosir, Mayuresh V Kothare, Srinivas Rangarajan | 2025 | Ind. Eng. Chem. Res. | integral, chemistry-constrained SINDy beats SINDy; stiffness vs sampling rate breaks all methods |
| S44 | DOI 10.3390/e23070824 | Masaki Ito, Tatsu Kuwatani, Ryosuke Oyanagi, Toshiaki Omori | 2021 | Entropy | adaptive Lasso + SMC selects terms with hidden solid states |
| S45 | arXiv:2101.06589; DOI 10.1016/j.jcp.2021.110743 | Juntao Huang, Yizhou Zhou, Wen-An Yong | 2021 | J. Comput. Phys. | multiscale reaction discovery traps optimisers; parameter-freezing fix |
| S46 | DOI 10.1021/acs.iecr.5c03704 | Katsoulas, K.; Galvanin, F.; Mazzei, L.; Sorensen, E. | 2026 | Ind. Eng. Chem. Res. | Lagrange-multiplier-test isotherm structure identification; flat-likelihood case |
| S47 | arXiv:2002.00790; DOI 10.1016/j.jcp.2021.110219 | Joseph Bakarji, Daniel M. Tartakovsky | 2021 | J. Comput. Phys. | constrained sparse learning of only the unknown closure |
| S48 | arXiv:2602.20413 | Kevin Slote, Jeremie Fish, Erik Bollt | 2026 | arXiv | KANDy: KAN + sparse-regression discovery |
| S49 | arXiv:2602.09988 | Enzo Nicolas Spotorno, Josafat Leal Filho, Antonio Augusto Medeiros Frohlich | 2026 | arXiv | KANs fragile, fail on multiplicative terms; MLPs better |
| S50 | arXiv:2511.07686 | Benjamin C. Koenig, Sili Deng | 2025 | arXiv | KA-CRNN learns 1-D parameter dependencies inside a mass-action structure |
| S51 | arXiv:2109.01634 | Cristina Cornelio, Sanjeeb Dash, Vernon Austel, Tyler Josephson, Joao Goncalves, Kenneth Clarkson, Nimrod Megiddo, Bachir El Khadir, Lior Horesh | 2021-23 | arXiv | theory-constrained SR rederives Langmuir |
| S52 | arXiv:2301.11919 | Charles Fox, Neil Tran, Nikki Nacion, Samiha Sharlin, Tyler R. Josephson | 2023 | arXiv | knowledge-constrained SR for adsorption equations |
| S53 | DOI 10.1137/130937913 | S. Stanhope, J. E. Rubin, D. Swigon | 2014 | SIAM J. Appl. Dyn. Syst. | single-trajectory identifiability; estimation sensitivity set by the data's spatial confinement |
| S54 | arXiv:2007.02848 | Daniel A. Messenger, David M. Bortz | 2020 | arXiv | WSINDy for PDEs; large-noise, poorly scaled data |
| S55 | arXiv:2206.00176 | Dimitris Bertsimas, Wes Gurnee | 2022 | arXiv | MIOSR: provably optimal L0 SINDy |
| S56 | arXiv:2302.10787 | Alan A. Kaptanoglu, Lanyue Zhang, Zachary G. Nicolaou, Urban Fasel, Steven L. Brunton | 2023 | arXiv | benchmark: STLSQ and MIO strong, weak form better; no dependence on scale separation |
| S57 | DOI 10.1002/cjce.24495 | Idelfonso B. R. Nogueira, Vinicius V. Santana, Ana M. Ribeiro, Alírio E. Rodrigues | 2022 | Can. J. Chem. Eng. | UODE for multicomponent fixed-bed adsorption from experiments |
| S58 | arXiv:2609.04011 | Arthur Jessop, Mohammed Alsubeihi, Ben Moseley, Ashwin Kumar Rajagopalan | 2026 | arXiv | differentiable FV hybrid learns constitutive laws from experiments |
| S61 | DOI 10.1016/j.chroma.2022.463037 | Sai Gokul Subraveti, Zukui Li, Vinay Prasad, Arvind Rajendran | 2022 | J. Chromatogr. A | PANACHE infers isotherms from dynamic column data |
| S63 | arXiv:2109.01050 | Aditi S. Krishnapriyan, Amir Gholami, Shandian Zhe, Robert M. Kirby, Michael W. Mahoney | 2021 | NeurIPS | PINN failure grows with reaction/convection coefficient (ill-conditioning) |
| S64 | DOI 10.1093/bioinformatics/btp358 | A. Raue, C. Kreutz, T. Maiwald, J. Bachmann, M. Schilling, U. Klingmüller, J. Timmer | 2009 | Bioinformatics | profile likelihood for structural/practical identifiability |
| S65 | arXiv:2107.02107 | Seth M. Hirsh, David A. Barajas-Solano, J. Nathan Kutz | 2021 | arXiv | UQ-SINDy: posterior inclusion probabilities via sparsifying priors |

Negative evidence from the search APIs (fetched): OpenAlex "sparse identification nonlinear dynamics adsorption" and
"symbolic regression adsorption kinetics", and the arXiv API query (adsorption AND SINDy / SR / equation discovery),
each surfaced exactly one adsorption-KINETICS discovery paper: S1.

## (b) Closest prior work to the candidate paper

Candidate: "When can AI discover adsorption kinetics from breakthrough data? An identifiability map for equation
discovery across Damköhler number and noise."

**Verdict, stated plainly.** No fetched paper does the candidate as a whole. None maps whether equation discovery
recovers the adsorption rate law as a function of Da and noise, and none uses a measured isotherm. But every
ingredient has precedent, and the physical headline ("near local equilibrium the mass-transfer coefficient is not
identifiable from breakthrough data") is CLASSICAL: S29, S36, S37, S8 and S33 already establish it. That sentence
must not be claimed as new. What is new is the quantitative discoverability boundary for strong discovery methods,
and the isotherm-error mechanism.

The five papers (or clusters) a referee would cite against novelty:

1. **Santana et al. 2023, Chem. Eng. Sci. (S1), with the same group's S57 (2022) and S42 (2025).**
   What it did: a UDE puts an NN in the uptake term of the column PDE, trained on outlet-only breakthrough data with 5 %
   noise. SINDy (Lasso/ADMM + BIC) and GP-SR then recover the LDF law with coefficients close to +/-0.22. The isotherm
   q* is supplied exactly. Attack: "AI discovery of LDF from breakthrough curves is already shown."
   How the candidate differs:
   (i) S1 is one point: one k, one noise level, Pe = 21. By our calculation (k = 0.22 min^-1, L = 2.0 dm,
   v = 0.51 dm/min) it has Da = kL/v ~ 0.9, which is kinetically controlled and below the candidate's 3.8-689 range.
   (ii) S1 assumes an exact q*. The candidate shows that recovery collapses when q* is measured (0.8 % error with exact
   q*, ~96 % with measured q*, at Da ~600).
   (iii) S1 reports success. The candidate says where and why discovery fails.
   Action: recompute S1's Da with the project's own definition and plot S1 on the map as an external point.

2. **Taylor, Herman & Morales 2026, J. Contam. Hydrol. (S35).**
   What it did: global sensitivity analysis of sorbing and degrading transport across Pe-Da regimes. Parameters
   include the desorption rate and Kd, and equilibrium sorption dominates the breakthrough.
   Attack: "regime maps of what breakthrough data can inform across Pe-Da already exist."
   How the candidate differs: it asks whether the rate-law STRUCTURE can be discovered (term selection, sign,
   sparsity), not how sensitive the output is to known parameters. It also adds nonlinear-isotherm adsorption columns,
   a noise axis and isotherm error.

3. **Knox et al. 2016, IECR (S8), and Ward & Pini 2022, Adsorption (S33).**
   What they did: from outlet breakthrough data, the LDF k and the axial dispersion can be extracted wrongly, and
   interior measurements are needed (S8). About 70 % of the output variance comes from isotherm parameters (S33).
   Attack: "adsorption engineers already know k is poorly determined by breakthrough curves."
   How the candidate differs: it turns this qualitative caveat into a map over Da and noise for discovery algorithms,
   and names the mechanism (isotherm error is comparable to the driving force).

4. **Katsoulas et al. 2023, J. Chromatogr. A (S29), with Valocchi 1985 (S37) and Hansen & Vesselinov 2017 (S36).**
   What they did: near local equilibrium, finite mass transfer enters only through an apparent dispersion coefficient
   (EDM derived asymptotically). Local-equilibrium validity is a question of whether mass-transfer dispersion is small
   next to hydrodynamic dispersion.
   Attack: "the map follows from classical local-equilibrium / EDM theory, so nothing is new."
   How the candidate must differ:
   - Derive the boundary from this theory (for example, the driving-force fraction set by Da against isotherm error
     and noise).
   - Then test whether ML discovery fails at the same boundary as classical parameter identifiability (profile
     likelihood), or earlier.
   A measured gap in which discoverability is lost before identifiability would be the genuinely new result.

5. **Delgado-Cano et al. 2025 (S15), with Stanhope et al. 2014 (S53), Gallo et al. 2026 (S11) and Klishin et al. 2024 (S12).**
   What they did: SINDy becomes ill-conditioned on slow manifolds (S15). Estimation sensitivity is set by the data's
   spatial confinement (S53). The smallest eigenvalue of the data moment matrix caps SINDy and PySR recovery (S11).
   Noise-induced phase transitions exist (S12).
   Attack: "this is the known generic failure of sparse regression on slow manifolds."
   How the candidate differs: it ties that conditioning to a physical design number (Da) in an engineering system,
   adds isotherm error as errors-in-variables, and covers the MOF-water case. It should measure lambda_min or the
   confinement condition number per grid cell and show that it predicts the boundary.

## (c) Gaps (each tied to evidence)

- **G1 (primary): no discoverability map for adsorption rate laws over Da and noise.**
  S1 is a single point (one k, one noise level). S35 maps parameter sensitivity, not discovery. Three fetched API
  searches (OpenAlex x2, arXiv) found no other adsorption-kinetics discovery paper.
- **G2: isotherm uncertainty has not been treated as errors-in-variables in discovery.**
  S1 fixes q*. S33 shows isotherm parameters dominate breakthrough variance. EIV-robust discovery and estimation exist
  in general (S13 ODR-BINDy, S22 WENDy) but has not been applied to adsorption.
- **G3: classical local-equilibrium theory has not been linked to discovery-failure theory.**
  The LEA / apparent-dispersion literature (S29, S36, S37) and the SINDy-conditioning theory (S11, S15, S53) never cite
  each other in the fetched abstracts. There is room for a predictor (lambda_min or a Gram condition number) as a
  function of Da and Pe.
- **G4: discoverability and identifiability have not been compared on the same grid.**
  Profile likelihood (S64), UDE functional identifiability (S10) and bootstrap multimodality (S3) exist, but none is
  mapped against a regime number alongside discovery success.
- **G5: no rate-law discovery for MOF/COF water.**
  MOF-303 water kinetics are fitted by hand with LDF, and the rate drops at the isotherm step (S39). SR exists only for
  isotherms (S4, including water on flexible adsorbents; S6, S51, S52) and for structure-to-uptake screening (S5). A
  2026 review of AI for MOF water harvesting is silent on kinetics discovery in its abstract (S41). A state-dependent
  k(q) near a step isotherm is an untested discovery target.
- **G6: the observation model is not realistic.**
  S8 says interior measurements are needed for reliable k. S1 used outlet data only. Latent-state discovery exists
  elsewhere (S20, S44). No adsorption study maps discoverability separately for outlet-only and interior-profile data.
- **G7: stiffness relative to sampling is not reported.**
  S43 reports that reactions faster than the sampling rate break every method. No adsorption discovery study reports
  1/k relative to the sampling interval, which is a second axis the map needs.
- **G8 (weak, search-only): PSA/TSA.**
  No SINDy or SR discovery for cyclic adsorption processes was found (SEEN-ONLY negative).

## (d) Recommended methods (strongest competitors; rule: compare against the strongest configuration)

**Discovery methods to include**, each in its strongest configuration:
1. **S1 reproduced (UDE + sparse/symbolic regression).** Train on outlet-only data with an NN uptake term, then run
   SINDy over a {1, q, q*, ...} library with BIC, and PySR. This is the direct prior-art pipeline. Use stronger SR
   settings than S1's as we read them (population 30, 30 iterations).
2. **Weak-form SINDy (S19; S54 for PDE).** The weak form wins the SINDy benchmark (S56) and handles poorly scaled
   data, which matters because q is much larger than c in MOF columns.
3. **Ensemble / Bayesian SINDy (S14 E-SINDy, S65 UQ-SINDy).** Report the inclusion probability of the (q*-q) term and
   the posterior probability of its correct sign. This is the natural per-cell metric for the map.
4. **Exact, constrained selection: MIOSR (S55).** Add the constraints k > 0 and zero rate at q = q*. Also use the
   Delahunt-Kutz handling of linearly dependent functionals (S38). This rules out "the optimiser failed" as the
   explanation for the observed non-sparsification and 69 % sign accuracy.
5. **Errors-in-variables methods: ODR-BINDy (S13) and WENDy-IRLS (S22).** These are the strongest direct answer to the
   measured-isotherm failure and must be tried before claiming it.
6. **SINDy-PI (S21)** for rational rate laws containing Langmuir, Toth or cooperative q*.
7. **Constrained and weak-form GP-SR:** PySR (S23) with physical constraints, and ADoK-W / PI-ADoK (S26, S27).
8. **Slow-manifold-aware discovery: SINDy on slow manifolds (S15) and CSP partitioning (S16).** At high Da this is the
   method expected to succeed, by returning the isotherm plus an effective dispersion rather than k. Including it lets
   the paper state what IS discoverable at high Da, not only what fails.
9. **KAN (secondary).** Use the KANDy configuration (KAN + sparse regression, S48). S49 reports fragility and failure
   on multiplicative terms, and S50 shows KANs work best inside a fixed structure, so KAN should not be the headline.
10. **PINN inverse** only with the S63 remedies (curriculum or seq2seq). Plain PINNs degrade at large reaction
    coefficients for optimisation reasons, which would confound the identifiability claim.

**Identifiability tools:**
- **Profile likelihood (S64)** for k, D_L and the isotherm parameters in every grid cell. This is the direct test of
  practical identifiability, and a flat k-profile at high Da is the expected signature.
- **Fisher information and Gram-matrix conditioning.** Use the FIM eigenvalues, the condition number of the discovery
  library's Gram matrix, lambda_min of the moment matrix (S11) and the spatial-confinement condition number (S53).
  These are cheap mechanistic predictors of the boundary.
- **UDE functional identifiability (S10)** for the UDE competitor.
- **Bayesian inference + Sobol (S33)**, which is the incumbent adsorption-engineering workflow.
- **Bootstrap ensembles (S3)** to detect multimodal solutions.
- **Lagrange-multiplier test (S46)** for "must k depend on state?", relevant to MOF step isotherms (S39).
- Not verified here: structural-identifiability software based on differential algebra. It was not fetched, so name it
  only after checking.

**Axes the map should carry:**
- Da AND Pe, or the ratio of kinetic to hydrodynamic dispersion (S29, S36, S37)
- noise sigma
- isotherm error eps_iso
- 1/k relative to the sampling interval (S43)
- observation model: outlet-only vs interior (S8)
- isotherm shape: favourable/constant pattern, where k is estimable from front width (S30), vs dispersive or step

## (e) Risks

- **R1. "Already known."** The mechanism is classical (S29, S36, S37, S8, S33).
  Mitigation: frame the contribution as a quantitative discoverability boundary plus a discoverability-vs-identifiability
  comparison. Never present "k is unidentifiable near equilibrium" as a discovery.
- **R2. S1 looks like a counterexample.** S1 recovered LDF at 5 % noise. Our Da ~0.9 estimate puts it in the kinetic
  regime, where the candidate also predicts success. Under a different Da definition (for example one that includes
  the solid capacity factor) the number changes. Recompute and plot it. If S1 lands inside the candidate's failure
  region, the contradiction is real and must be explained.
- **R3. Straw-man competitor.** The failing configuration (column-standardised polynomial SINDy) is not the strongest.
  S55 and S56 show the optimiser matters, S19 and S54 that the weak form matters, and S13 and S22 that EIV handling
  matters. Standardising nearly collinear q and q* columns can itself worsen selection (S38). Unless methods 2-5 are
  run, a referee will blame the method rather than identifiability.
- **R4. Da may be the wrong single axis.** For favourable isotherms in the constant-pattern regime, k is estimable from
  front width by fitting (S30). The kinetic effect only disappears when swamped by hydrodynamic dispersion (S36), so
  Pe and isotherm shape matter. Step (S-shaped) MOF isotherms mix dispersive and self-sharpening fronts.
- **R5. Counter-evidence from S56.** SINDy success did not depend on scale separation across chaotic benchmarks. The
  paper must argue that breakthrough data differ: they are transient single trajectories confined to a slow manifold
  (S53, S11, S15), not attractor-filling data.
- **R6. An EIV method might rescue recovery.** If ODR-BINDy or WENDy recover k from a measured isotherm at moderate Da,
  the "fails from a measured isotherm" headline must be restated as a law: the isotherm error must stay below the
  driving-force fraction.
- **R7. Synthetic optimism.** If the map uses interior c and q fields from the solver, it overstates what experiments
  can deliver: S8 flags non-plug flow and the need for interior probes, and S1 used outlet data only.
- **R8. Scoop risk (moderate).** Active groups are publishing close work: the Santana/Nogueira group (S1, S42, S57), a
  differentiable-hybrid adsorption-process group (S58, Sep 2026), discovery-identifiability theory (S11, Jul 2026)
  and Pe-Da sensitivity (S35, Nov 2026).
- **R9. Limits of this review.**
  - Several classical sources are metadata-only or SEEN-ONLY: S7 (Sircar & Hufton), S32, S34, S40, S59 and S60.
  - Some abstracts were reconstructed by OpenAlex and paraphrased by the fetch tool: S31 and S37 are marked (low).
  - Full text was read only for S1 (arXiv HTML, through a summarising fetch), S43, S44 and S46 (PMC).
  - ACS, Elsevier, Wiley and Springer pages returned 403 or a login redirect.
  - Google Scholar was not queried.
  - So "nobody has done X" rests on three fetched API searches plus web searches. It is not a proof.

## Proposed one-sentence differentiator (for the paper)

"Unlike single-regime demonstrations (S1) and parameter-sensitivity maps (S35), we map when the adsorption rate LAW
is discoverable across Damköhler number, Péclet number, noise and isotherm error, for the strongest sparse, weak-form,
errors-in-variables and symbolic methods. We show that the discoverability boundary is predicted by
[profile-likelihood / Gram-conditioning] identifiability and is set by the isotherm error relative to the
equilibrium driving force."
