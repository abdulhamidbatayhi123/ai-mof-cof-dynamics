# Literature update for Paper 2 (discoverability of the adsorption rate law), 12 October 2026

Scope: new sources that Paper 2 (`paper2/stage1.tex`) should know about. Sources already in
`research/lit_equation_discovery.md` (S1-S65) or in the stage1.tex bibliography are not repeated, except where a
newer version or a correction matters.

Method. Searches ran on 12 Oct 2026 against the OpenAlex API (title/abstract search, full-text search, author
listings, and forward-citation searches `cites:` on Santana 2023, Knox 2016, Abu El-Maaty 2024 and
Fajardo-Fontiveros 2023), the arXiv API (titles and abstracts), the Crossref API (DOI metadata), the Semantic Scholar
API (rate-limited; used only for single records) and web search. No personal data was sent in any request.
Every entry below was opened as a record. The **Verified** line says what was read:
- `ABSTRACT (API)`: the abstract was read from arXiv, Crossref or OpenAlex, and the DOI or arXiv id was resolved.
- `FULL TEXT`: the PDF was opened and the quoted passages were found in it.
- `METADATA ONLY`: the DOI was resolved (title, authors, venue), but no abstract was available. Content
  claims for these entries are marked as coming from a secondary snippet, and they are not evidence.

Tags: **SCOOP RISK** / **MUST CITE** / **SHOULD CITE** / **BACKGROUND**.

---

## 1. Equation or symbolic discovery for sorption, chromatography and transport, and hybrid column models

### N1. Strouwen & Micluta-Campeanu 2025, IFAC-PapersOnLine. "Experimental Design for Missing Physics". **SHOULD CITE**
- DOI 10.1016/j.ifacol.2025.07.192. Verified: ABSTRACT (API, OpenAlex). Found as a forward citation of Santana 2023.
- What it says: the UDE + symbolic-regression pipeline "require[s] high-quality data to successfully recover the true
  model structure". It builds a sequential experimental design that discriminates between the plausible structures
  that symbolic regression proposes, and applies it to a bioreactor.
- Why it matters: it is the first design-of-experiments answer to "UDE+SR discovery fails on uninformative data". It
  is the natural forward link for the Discussion: where the map shows discovery failing, design can move the data.
  Not a scoop: it has no adsorption content and no regime map.

### N2. Lamb et al. 2026, Science Advances. "Discovering how ice crystals grow using neural ODEs and symbolic regression". **SHOULD CITE**
- DOI 10.1126/sciadv.aee6174. Verified: ABSTRACT (API, OpenAlex).
- What it says: a neural ODE inside a depositional growth model, trained on 290 levitated-crystal mass time series and
  read out by symbolic regression, gives a "modified capacitance growth model". The model generalizes to independent
  AIDA chamber data.
- Why it matters: a high-profile success of the M1 recipe (UDE, then a symbolic read-out) on a sorption-like uptake
  law, using real data. It is the best recent counterweight to the negative framing, and a Nature-family editor will
  know it.

### N3. Matias, Ferreira, Nogueira & Ribeiro 2025, Systems and Control Transactions. "A Novel AI-Driven Approach for Parameter Estimation in Gas-Phase Fixed-Bed Experiments". **BACKGROUND**
- DOI 10.69997/sct.156880. Verified: ABSTRACT (API).
- What it says: an AI-based optimiser estimates the *isotherm* parameters of a phenomenological fixed-bed model
  (CO2/CH4). The rate law is not discovered.
- Why it matters: this is the most recent fixed-bed paper from the Santana/Nogueira group, found by listing the
  group's 2024-2026 output. None of their 2024-2026 titles is a regime map of rate-law discovery, so the group
  looks like a low scoop risk at present.

### N4. Guo et al. 2026, Sep. Purif. Technol. 383:136143. "Full dynamic breakthrough behaviors of CO2/N2 adsorptions on CMS and SG predicted by an experimentally validated hybrid neural network". **BACKGROUND**
- DOI 10.1016/j.seppur.2025.136143. Verified: METADATA ONLY (Crossref; no abstract available).
- Why it matters: this is the current breakthrough "hybrid NN" literature, which is prediction-oriented. Cite it only
  if the abstract is read first.

### N5. Panahi, Porta, Riva & Guadagnini 2026, arXiv:2608.17591. "Probabilistic Inverse Modeling of Contaminant Transport via a Conditioned-on-Design Bayesian PINN". **SHOULD CITE**
- arXiv:2608.17591. Verified: ABSTRACT (API).
- What it says: a Bayesian PINN applied to laboratory column breakthrough data. It finds that effective sorption
  capacity depends on flow rate "consistent with kinetic limitations". It reports "a strong negative correlation
  between sorption affinity and sorption capacity, quantifying the intrinsic non-identifiability of the inverse
  problem".
- Why it matters: 2026 evidence, on real column data, that equilibrium and kinetic parameters trade off. This
  supports the paper's decision to treat isotherm error as a regressor error.

### N6. Liu et al. 2026, Groundwater for Sustainable Development 34:101679. "From curve fitting to scientific machine learning: A critical synthesis of solute transport modeling and breakthrough curve interpretation". **SHOULD CITE**
- DOI 10.1016/j.gsd.2026.101679. Verified: ABSTRACT (API, OpenAlex).
- What it says: interpretations that rely "exclusively on boundary outlet sampling" suffer from "severe mathematical
  ill-posedness and equifinality". Resolving this "necessitates a methodological transition toward high-dimensional
  internal sensing". "Dimensionless indicators and BTC morphology are used to narrow the set of plausible models."
- Why it matters: a 2026 review that independently supports the paper's O1/O2/O3 design and its use of dimensionless
  groups. It is a review, so it reports no new evidence of its own.

### N7. Wang, Gong, Qiu & Qin 2026, arXiv:2609.21234. "Discovery of an explicit closure dispersion model for contrast-agent transport in arteries". **BACKGROUND**
- arXiv:2609.21234. Verified: ABSTRACT (API).
- What it says: symbolic regression finds a 1-D effective dispersion closure that holds at high Peclet number, where
  Taylor-Aris fails.
- Why it matters: symbolic regression of a *transport* closure organised by a dimensionless group (Pe). The success
  is reported by regime, but no discoverability map is drawn. Low scoop risk.

### N8. Palma Banos, Kress, Hernandez & Craven 2026, Digital Discovery 5:2325-2341. "Stoichiometrically-informed symbolic regression for extracting chemical reaction mechanisms from data". **SHOULD CITE**
- DOI 10.1039/d5dd00470e; arXiv:2510.20655. Verified: FULL TEXT (arXiv PDF). Passage found: "if there are rate
  constants that differ by multiple orders of magnitude the SINDy approach will generally prune the slow process from
  the derived dynamical system". Their own fast/slow test reports that SISR captures fast/slow dynamics better than
  thresholding methods, but only because samples are taken in the fast region.
- Why it matters: direct support for the claim that time-scale separation breaks rate-law discovery. It sits next to
  `prabhu2025` and `huang2021` and appeared in Digital Discovery, a target-venue journal.

### N9. Kim & Deng 2024, Nature Communications. "Learning reaction-transport coupling from thermal waves". **SHOULD CITE**
- DOI 10.1038/s41467-024-54177-2. Verified: ABSTRACT (API).
- What it says: thermal properties and chemical kinetics are learned from thermal-wave dynamics by PDE-constrained
  optimisation, "without the need for a comprehensive measurement of all state variables".
- Why it matters: a Nature-family precedent for learning a reaction rate from travelling-front data with latent
  states, the reaction analogue of O2/O3. It estimates parameters within a fixed model space and does not discover
  structure.

### N10. Lin, Wang & Deng 2025, npj Computational Materials. "Neural ODEs for smooth, high-accuracy isotherm reconstruction, interpolation, and extrapolation" (IsothermODE). **BACKGROUND**
- DOI 10.1038/s41524-025-01819-8. Verified: ABSTRACT (API).
- What it says: a neural ODE reconstructs CO2/MOF isotherms from five pressure points, with uncertainty
  quantification.
- Why it matters: the equilibrium side again. It is one more route to the *measured* isotherm `q*_meas` whose error
  the paper treats.

---

## 2. Theory and benchmarks of discoverability and identifiability limits

### N11. Shumaylov, Zaika, Scholl, Kutyniok, Horesh & Schonlieb 2025, arXiv:2511.08860. "When is a System Discoverable from Data? Discovery Requires Chaos". **MUST CITE** (the closest theoretical competitor to the paper's framing)
- arXiv:2511.08860 (v2). Verified: FULL TEXT (arXiv PDF). Venue: none shown on arXiv. Treat it as a preprint.
- What it says: systems chaotic on their whole domain are discoverable from one trajectory within continuous
  functions. Theorem 6.1: "If an analytic vector field F admits a non-constant global analytic first integral G, then no
  trajectory of F is a set of uniqueness, and thus F is not analytically discoverable." The authors argue that "The
  prevalence of chaotic systems in benchmark datasets may have inadvertently obscured this fundamental limitation".
  For non-chaotic systems, "certain prior physical knowledge can nonetheless recover uniqueness". They name digital
  twins of stable engineering systems as the hard case.
- Why it matters: (i) a breakthrough run is a stable, non-chaotic transient that converges to equilibrium, so this
  paper predicts that trajectory data alone cannot determine its law uniquely. (ii) It explains why `kaptanoglu2023`
  found no scale-separation effect on chaotic benchmarks, which the Introduction currently presents as
  counter-evidence. (iii) It justifies Lib-B (`q*_meas` as a prior) as exactly the kind of prior knowledge that
  restores uniqueness. Not a scoop: it has no adsorption content, no regime grid and no comparison with
  identifiability.

### N12. Loman, Browning & Baker 2026, arXiv:2606.30289. "Structural functional identifiability and model discovery in differential equation models". **MUST CITE**
- arXiv:2606.30289. Verified: ABSTRACT (API).
- What it says: it generalises structural parameter identifiability to *functional* identifiability. It finds "broad
  classes of models for which unique functional recovery is impossible" and uses differential algebra to assess it.
  It describes phenomena "that have no analogue in the classical setting".
- Why it matters: it is the theoretical bridge between H2b's two sides (law discoverability against parameter
  identifiability). It extends `loman2025`, which is already cited. A referee will ask whether the k(q) of H2d is
  structurally functionally identifiable from O1/O2/O3 at all.

### N13. Lou et al. 2026, arXiv:2606.09638. "Data-driven discovery of governing differential equations across physical systems" (Review). **SHOULD CITE**; **figure model**
- arXiv:2606.09638. Verified: ABSTRACT (API).
- What it says: it proposes "a two-dimensional phase diagram of equation discoverability" that organises problems by
  structural complexity and coefficient complexity. It explains "why different methodological families succeed or
  fail in different problem settings".
- Why it matters: the field now uses the phrase "phase diagram of discoverability". Paper 2's map is a *quantitative,
  physics-axis* version of it (Da, Pe, sigma, epsilon). Cite it and position the paper against it. This is a mild
  wording scoop: the term is taken, but the content is not.

### N14. Fajardo-Fontiveros, Reichardt, De Los Rios, Duch, Sales-Pardo & Guimera 2023, Nature Communications 14:1043. "Fundamental limits to learning closed-form mathematical models from data". **MUST CITE**
- DOI 10.1038/s41467-023-36657-z; arXiv:2204.02704. Verified: ABSTRACT (Crossref, arXiv).
- What it says: model learning shows "a transition from a low-noise phase in which the true model can be learned, to
  a phase in which the observation noise is too high for the true model to be learned by any method". Probabilistic
  model selection generalises optimally in both phases. "In the transition region ... generalization is hard for all
  approaches including probabilistic model selection".
- Why it matters: the Nature-family precedent for a *learnability phase transition in noise*. H2a's 50 % crossing in
  R is the same object, conditioned on physics axes. It also implies that a Bayesian / probabilistic model-selection
  method (the Bayesian machine scientist) is the "strongest configuration" competitor an editor will expect (see
  Implications).

### N15. Messenger & Bortz 2024, IMA Journal of Numerical Analysis. "Asymptotic consistency of the WSINDy algorithm in the limit of continuum data". **MUST CITE**
- DOI 10.1093/imanum/drae086. Verified: ABSTRACT (API).
- What it says: WSINDy is unconditionally consistent for a class of models, but "in general ... only conditionally
  asymptotically consistent, yielding discovery of spurious terms with probability one if the noise level exceeds a
  critical threshold sigma_c". It gives explicit bounds on sigma_c and shows that light denoising restores
  consistency.
- Why it matters: a *proved* noise boundary for M2, the paper's weak-form method. H2a's R* is an empirical analogue of
  it. Compare the measured sigma boundary of M2 with the sigma_c bound, or at least state that it exists.

### N16. Casolo, Becker & Kilbertus 2026, ICLR 2026. "Identifiability Challenges in Sparse Linear Ordinary Differential Equations". **SHOULD CITE**
- arXiv:2506.09816 (journal ref ICLR 2026). Verified: ABSTRACT (API).
- What it says: unlike dense linear ODEs, "sparse systems are unidentifiable with a positive probability in
  practically relevant sparsity regimes". "Theoretical limitations are not resolved through inductive biases or
  optimization dynamics."
- Why it matters: sparsity, the very prior SINDy uses, can create non-identifiability. This is relevant to the support
  {q*_meas, q} in a library that contains c and q^2.

### N17. Gao, Fasel, Brunton & Kutz 2023, arXiv:2301.12649. "Convergence of uncertainty estimates in Ensemble and Bayesian sparse model discovery". **SHOULD CITE**
- arXiv:2301.12649. Verified: ABSTRACT (API).
- What it says: bootstrapped STLSQ (the E-SINDy that M3 uses) "can perform a provably correct variable selection
  procedure with an exponential convergence rate of the error rate", and its inclusion probabilities converge to a
  delta at the truth as the sample size grows.
- Why it matters: this is the theory behind M3's inclusion-probability report. Cite it where M3's 0.6 threshold is
  set.

### N18. Champneys & Rogers 2025, Proc. R. Soc. A 481:20240620. "BINDy: Bayesian identification of nonlinear dynamics with reversible-jump Markov-chain Monte Carlo". **SHOULD CITE** (missing competitor)
- DOI 10.1098/rspa.2024.0620; arXiv:2408.08062. Verified: ABSTRACT (Crossref).
- What it says: a full joint posterior over library terms and coefficients via reversible-jump MCMC, sparse "in the
  model space rather than in parameter space". It "compare[s] favourably to ensemble SINDy" and assigns higher
  probability to correct terms.
- Why it matters: it is now the strongest Bayesian SINDy in a top journal. M3 cites `hirsh2021`, but bagged STLSQ
  is implemented. (The ODR-BINDy of `fung2026` is a different "BINDy" that builds on this one.)

### N19. Islam, Nishino, Shiraishi & Takeuchi 2026, arXiv:2610.11486. "PSI-SINDy: Post-Selection Inference for Sparse Identification of Nonlinear Dynamics". **SHOULD CITE**
- arXiv:2610.11486 (posted 8 Oct 2026). Verified: ABSTRACT (API).
- What it says: "using the same noisy trajectory for both selecting dynamical terms and assessing their statistical
  significance can introduce selection bias". It splits one trajectory into four independent views by data thinning,
  which handles "measurement error in the candidate terms and shared noise between the response and design".
- Why it matters: the same concern as the paper's selection/estimation split (amendment A1), and it explicitly names
  regressor measurement error (the EIV issue of H2c). Cite it in the A1 rationale.

### N20. Zhang, Li & Carvalho 2026, arXiv:2604.11929. "Fast and principled equation discovery from chaos to climate" (Bayesian-ARGOS). **BACKGROUND**
- arXiv:2604.11929. Verified: ABSTRACT (API).
- What it says: frequentist screening followed by Bayesian inference. It beats SINDy in data efficiency on all seven
  chaotic systems tested, and gives diagnostics for "influence analysis and multicollinearity detection that expose
  failure modes otherwise opaque".
- Why it matters: multicollinearity diagnostics are what the paper's Gram-matrix predictor (Methods §mech) does. This
  is a possible additional competitor.

### N21. d'Ascoli, Becker, Mathis, Schwaller & Kilbertus 2024, ICLR 2024. "ODEFormer: Symbolic Regression of Dynamical Systems with Transformers" (introduces **ODEBench**). **SHOULD CITE**
- arXiv:2310.05573. Verified: ABSTRACT (API); the ICLR 2024 proceedings listing was seen in search.
- What it says: ODEBench is 63 ODEs (1-4-D) curated to fix the Strogatz set's problems. ODEFormer "consistently
  outperforms existing methods while displaying substantially improved robustness to noisy and irregularly sampled
  observations".
- Why it matters: ODEBench is the standard benchmark for ODE symbolic regression. A referee may ask how the
  harness's methods score on a standard benchmark before they are trusted on the grid (see Implications).

### N22. Aldeia et al. 2025, GECCO Companion 2025:2529-2538. "Call for Action: towards the next generation of symbolic regression benchmark" (SRBench 2.0). **SHOULD CITE**
- DOI 10.1145/3712255.3734309; arXiv:2505.03977. Verified: ABSTRACT (arXiv) plus DOI (Crossref).
- What it says: an updated SRBench with nearly twice as many methods. "No single algorithm dominates across all
  datasets." It calls for standardised hyperparameter tuning, execution constraints and compute allocation.
- Why it matters: it backs the paper's "strongest configuration", cost gates and fixed-budget rules. It also argues
  against a single best method, which supports per-slice selection.

### N23. Shojaee et al. 2025, ICML 2025 (PMLR 267). "LLM-SRBench: A New Benchmark for Scientific Equation Discovery with Large Language Models". **BACKGROUND / SHOULD CITE if LLM-SR is mentioned**
- arXiv:2504.10415. Verified: ABSTRACT (API).
- What it says: existing benchmarks are "susceptible to memorization by LLMs". The best system reaches "only 31.5%
  symbolic accuracy".
- Why it matters: LDF and Langmuir are textbook laws, so any LLM-based competitor (including `sharlin2024`, cited)
  could memorise them. If LLM methods are mentioned, say this.

### N24. Ruan et al. 2026, Nature Computational Science 6:53-66. "Discovering physical laws with parallel symbolic enumeration" (PSE). **SHOULD CITE**
- DOI 10.1038/s43588-025-00904-8. Verified: ABSTRACT (API, OpenAlex). The volume and page numbers come from a search
  snippet.
- What it says: PSE improves recovery accuracy "by up to 99%" and runtime by an order of magnitude over
  state-of-the-art baselines, across more than 200 problem sets.
- Why it matters: a current Nature-family symbolic-regression method. It shows that PySR is not uncontested as "the
  strongest" symbolic-regression method.

### N25. Yu, Ding & Li 2025/2026, Nature Computational Science 6:156-168. "Discovering network dynamics with neural symbolic regression". **BACKGROUND**
- DOI 10.1038/s43588-025-00893-8. Verified: METADATA ONLY (Semantic Scholar: venue, volume and pages; abstract elided).

### N26. Rummel, Messenger, Becker, Dukic & Bortz 2025, arXiv:2502.08881. "WENDy for Nonlinear-in-Parameters ODEs" (WENDy-MLE, WENDy.jl). **MUST CITE** (relevant to the "WENDy NOT RUN" rule)
- arXiv:2502.08881 (v3). Verified: ABSTRACT (API).
- What it says: WENDy-MLE approximates the maximum-likelihood estimator, handles multiplicative log-normal noise, and
  has "better accuracy, a substantially larger domain of convergence" than other weak-form methods and output-error
  least squares. It is implemented in Julia (WENDy.jl).
- Why it matters: Methods says WENDy will be reported NOT RUN "if no implementation is verified on its authors' own
  example". A maintained Julia implementation now exists, and the paper already has an isolated Julia environment for
  PySR. A referee will ask why it was not run.

### N27. Kaheman, Brunton & Kutz 2022, Mach. Learn.: Sci. Technol. 3:015031. "Automatic differentiation to simultaneously identify nonlinear dynamics and extract noise probability distributions from data" (modified SINDy). **SHOULD CITE**
- DOI 10.1088/2632-2153/ac567a. Verified: ABSTRACT (Crossref).
- What it says: it denoises, learns the noise distribution, and identifies the model in one optimisation. It is
  "approximately twice as robust to noise", up to 40 % noise.
- Why it matters: `fung2026` names modified-SINDy as a prior errors-in-variables (EIV) approach. Listing it completes
  the EIV family that H2c refers to.

### N28. Fung 2025, arXiv:2507.23426. "Overcoming error-in-variable problem in data-driven model discovery by orthogonal distance regression". **(already cited as `fung2026`; note)**
- arXiv:2507.23426. Verified: ABSTRACT (API).
- Note: the abstract says linear-regression discovery "assumes that all noise resides in the training target ... whereas
  the measurement noise is in the states (the regressors)". The arXiv abstract reports ODR-BINDy recovering Lorenz at
  up to 30 % noise. Checked on Crossref: DOI 10.1145/3831701 (ACM TAIS, 18 Jul 2026, "Overcoming error-in-variable or
  stiffness problem in SINDy-like data-driven model discovery") has the same abstract opening. It is the published
  version of this preprint under a retitled name, so the bibliography entry is correct. It names modified-SINDy (N27)
  and DySMHO as earlier EIV approaches.

### N29. Massonis, Villaverde & Banga 2023, PLoS Computational Biology. "Distilling identifiable and interpretable dynamic models from biological data". **SHOULD CITE**
- DOI 10.1371/journal.pcbi.1011014. Verified: ABSTRACT (API).
- What it says: it combines SINDy-PI with structural identifiability and observability analysis to discover models
  that are structurally identifiable and observable.
- Why it matters: precedent for coupling discovery with identifiability. It is the closest prior work to H2b in
  spirit, but it is a *filter*, not a *boundary comparison*. It also uses M6's method.

### N30. Yuan & Benyahia 2026, Systems and Control Transactions. "Comprehensive Framework for Model Discovery and Discrimination Based on Symbolic Regression and Structural Identifiability: Application to a Partially Observed Chemical Reaction System". **SHOULD CITE**
- DOI 10.69997/sct.170869. Verified: ABSTRACT (API).
- What it says: "structural identifiability and observability (SIO) ... is often overlooked in SR". It proposes
  SR+SIO on a partially observed sulfide-oxidation system.
- Why it matters: like N29, it pairs discovery with identifiability, but in chemical kinetics with latent states (the
  O2 situation). It is a mild competitor for the discovery-plus-identifiability framing. It has no regime map.

### N31. Heitzman-Breen, Dukic & Bortz 2025, arXiv:2506.17373. "A practical identifiability criterion leveraging weak-form parameter estimation". **SHOULD CITE**
- arXiv:2506.17373 (v5). Verified: ABSTRACT (API).
- What it says: it defines "(e, q)-identifiability", with e the observation noise and q the mean-square error of the
  estimator. It assesses practical identifiability with WENDy "far more quickly" than output-error methods, for
  systems with unobserved variables.
- Why it matters: an alternative to the paper's profile-likelihood [k/2, 2k] criterion that is explicitly
  noise-indexed, and a cheap route for O2/O3, where the paper has only 3 profile replicates. Cite it as the
  alternative criterion considered.

### N32. Aguilar, Munoz & Azaele 2026, Physical Review X. "Limits of Inference in Complex Systems: When Stochastic Models Become Indistinguishable". **SHOULD CITE**
- DOI 10.1103/tmkr-9kl2. Verified: ABSTRACT (API).
- What it says: experimental design (sampling frequency, dataset size) governs model distinguishability, with "sharp,
  resolution-dependent limits beyond which competing models become empirically indistinguishable".
- Why it matters: a high-impact 2026 statement of the same kind of boundary, with sampling as the axis. It supports
  the paper's choice to fix sampling at 200 times and to state that the boundary is conditional on it.

### N33. Guimera & Sales-Pardo 2026, Phil. Trans. R. Soc. A. "Bayesian symbolic regression: automated equation discovery from a physicist's perspective". **SHOULD CITE**
- DOI 10.1098/rsta.2025.0089. Verified: ABSTRACT (API).
- What it says: probabilistic symbolic regression "provides guarantees of performance that heuristic approaches lack"
  and "compels us to consider model ensembles, as opposed to single models".
- Why it matters: it comes from the theme issue "Symbolic regression in the physical sciences" and argues for
  ensemble outputs, which supports reporting inclusion probabilities rather than one selected law.

### N34. Brum, Lober, Previdelli & Rodrigues 2025, arXiv:2508.20257. "Discovering equations from data: symbolic regression in dynamical systems". **BACKGROUND**
- arXiv:2508.20257. Verified: ABSTRACT (API).
- What it says: five symbolic-regression methods tested on nine processes. PySR is "the most suitable".
- Why it matters: independent support for choosing PySR as M7.

### N35. Messenger, Bortz and others: the weak-form claims. **(no new entry)** The WSINDy noise-robustness claims are
covered by `messenger2021ode/pde` (cited) and N15.

### N36. Amaral, Grapiglia & Oishi 2026, arXiv:2606.28584 (ILTS-SINDy, outlier-robust); Basiri & Nicholson 2026, arXiv:2605.09696 (AutoSINDy: PySR proposes the library, SINDy selects); Billa, Guidetti & Mandreoli 2026, arXiv:2610.10931 (coefficient calibration as selection pressure in symbolic regression). **BACKGROUND**
- Verified: ABSTRACT (API) for all three.
- AutoSINDy reports "a ground-truth recovery rate of 92.8%". It is a hybrid of M7 and M2-M4 that the paper does not
  run. Mention it only if a referee asks about hybrids.

---

## 3. Practical identifiability of mass-transfer / LDF coefficients from breakthrough curves, and design of experiments

### N37. Wang & Dowling 2022, AIChE Journal 68(12):e17813. "Pyomo.DOE: An open-source package for model-based design of experiments in Python". **MUST CITE**
- DOI 10.1002/aic.17813. Verified: ABSTRACT (API).
- What it says: "the first application of MBDoE to fixed-bed breakthrough experiments", for "large-scale partial
  differential-algebraic equation (PDAE) models". It approximates the Fisher information matrix with k_aug. A search
  snippet of the paper adds that its case study calibrates a CO2/MOF breakthrough model.
- Why it matters: Fisher-information identifiability and design for breakthrough experiments already exist in
  AIChE J. Paper 2's identifiability side (profile likelihood only) should cite it. FIM eigenvalues of k per cell are
  a cheap metric that the chemical-engineering audience expects (see Implications).

### N38. DeJaco, McGivern, Manion, Siderius, Nguyen & Kearsley 2025, Chem. Eng. Sci. "A minimal-parameterization of the single-solute breakthrough-curve model: Statistical and predictive inference". **SHOULD CITE**
- DOI 10.1016/j.ces.2025.121772. Verified: METADATA ONLY (OpenAlex and Semantic Scholar; abstract elided). Content
  seen only through the AIChE 2024 abstract of the same authors, in a search snippet: a spline isotherm "closest
  thermodynamically consistent" to the data, a rate constant per experiment treated as a random variable, and
  posterior estimation by quadrature. Not evidence until the paper is read.
- Why it matters: the closest current work on the *statistical identifiability of the rate constant from
  breakthrough curves* (NIST, CES). Read it before Stage 2.

### N39. DeJaco & Kearsley 2023, Commun. Nonlinear Sci. Numer. Simul. 131:107794. "Understanding fast adsorption in single-solute breakthrough curves". **SHOULD CITE**
- DOI 10.1016/j.cnsns.2023.107794. Verified: ABSTRACT (API).
- What it says: in the small-epsilon limit, where "a dilute solute travels from fluid to solid much faster than along
  the column" (high Da), the popular approximations are regular perturbation and boundary-layer theory. It extends
  them to isotherms with inflection points. Shocks show no positive convergence order.
- Why it matters: the asymptotics of the high-Da limit, including inflected (step) isotherms. It is the
  breakthrough-curve counterpart of `katsoulas2023` and directly relevant to the step isotherm at high Da.

### N40. Krishna 2026, Chem. Eng. J. Advances. "Analysis of transient breakthroughs in fixed-bed adsorbers". **BACKGROUND**
- DOI 10.1016/j.ceja.2026.101431. Verified: ABSTRACT (API).
- What it says: "sharp" experimental breakthroughs are "a strong indication of the absence of intra-crystalline
  diffusion influences". Kinetically driven separations require Maxwell-Stefan thermodynamic coupling.
- Why it matters: practitioners already read the absence of kinetic information off sharp fronts (the high-Da side).

### N41. Buchner & Pini 2026, Langmuir 42:14716-14732. "Unary and Binary Dynamic Column Breakthrough Experiments with Carbon Dioxide and Nitrogen Imaged by X-ray Computed Tomography". **MUST CITE**
- DOI 10.1021/acs.langmuir.6c00250. Verified: ABSTRACT (Semantic Scholar; Crossref metadata). Found as a forward
  citation of Knox 2016.
- What it says: the "digital adsorption" method (adsorption plus X-ray CT) describes "the transient progression of
  the internal adsorbed phase" in dynamic column breakthrough experiments. Binary CO2-N2 runs, with a 1-D model,
  capture "fast N2 and slower CO2 uptake, as well as a thermally enhanced roll-up".
- Why it matters: **experimental evidence that O1 (interior adsorbed loading q(z,t)) can be measured**. The paper
  currently calls O1 "the optimistic ceiling". This shows it is a real, if specialised, observation model, and it
  answers the "synthetic optimism" objection (risk R7 in the old review). The earlier method paper is Joss & Pini 2017,
  J. Phys. Chem. C, "Digital Adsorption: 3D Imaging of Gas Adsorption Isotherms by X-ray Computed Tomography", DOI
  10.1021/acs.jpcc.7b09836 (ABSTRACT verified).

### N42. Liu, Maini & Baker 2025, arXiv:2506.11311. "Optimal experiment design for practical parameter identifiability and model discrimination". **SHOULD CITE**
- arXiv:2506.11311. Verified: ABSTRACT (API).
- What it says: it designs control inputs that maximise profile-likelihood identifiability, and treats design for model
  discrimination as an optimal-control problem (Pontryagin).
- Why it matters: the profile-likelihood OED counterpart. It supports a Discussion point that the inlet programme (a
  step) is a design choice, and that discoverability could be designed for.

### N43. Simpson & Maclaren 2023, PLoS Computational Biology. "Profile-Wise Analysis: a profile likelihood-based workflow for identifiability analysis, estimation, and prediction". **SHOULD CITE**
- DOI 10.1371/journal.pcbi.1011515. Verified: ABSTRACT (API).
- Why it matters: the current standard profile-likelihood workflow. It sits next to `raue2009` for the paper's
  identifiability criterion.

### N44. Canzano, Iovino, Leone, Salvestrini & Capasso 2012, Adsorption Science & Technology 30:217-225. "Use and Misuse of Sorption Kinetic Data: A Common Mistake That Should Be Avoided". **SHOULD CITE** (classical adsorption precedent for "near equilibrium the rate law is undetermined")
- DOI 10.1260/0263-6174.30.3.217. Verified: ABSTRACT (Crossref).
- What it says: numerical simulation shows that using data "at (or very close to) equilibrium in the search for the
  kinetic equation ... frequently leads to incorrect conclusions". The t/q_t-against-t fit "is a straight line
  irrespective of the sorption kinetics".
- Why it matters: in batch adsorption kinetics, it is long known that near-equilibrium data cannot discriminate
  rate-law forms. This is the batch analogue of the paper's mechanism (driving force small against error). Cite it in
  "What is known and what is not new". Related: Simonin 2016, Chem. Eng. J. 300:254-263, DOI
  10.1016/j.cej.2016.04.079 (METADATA ONLY): the PFO/PSO comparison bias.

### N45. Hyun, Jung & Choi 2025 (in the old review as S34, METADATA ONLY) now has a companion: Hyun et al. 2025, Sep. Purif. Technol., "Mechanism-resolved modeling of dual-functional gas purification: a physics-aware Bayesian predictive framework using breakthrough curves", DOI 10.1016/j.seppur.2025.135612 (METADATA ONLY). A search snippet says that "different parameter combinations can yield similar profiles", with trade-offs between a lumped mass-transfer coefficient and an apparent rate. Read it before citing.

### N46. Shen & Thibault 2026, Separations 13:100. "Modelling Adsorption Breakthrough Curves". **BACKGROUND**
- DOI 10.3390/separations13030100. Verified: ABSTRACT (API).
- What it says: five rate models (instantaneous, LDF-type, Fickian, fractional/anomalous) were fitted to butanol on
  activated carbon. "Model performance depended strongly on the adsorbent type."
- Why it matters: rate-law choice from breakthrough curves is still done by hand-comparing a few candidates in 2026.

### N47. Jin et al. 2026, Research Square preprint. "Simultaneous Estimation of LDF Mass Transfer Coefficients and Multicomponent Isotherm Parameters from Breakthrough Curves Using a Two-Stage Strategy". **BACKGROUND (unread)**
- DOI 10.21203/rs.3.rs-10565594/v1. Verified: METADATA ONLY (title and DOI via OpenAlex; the abstract did not load).

---

## 4. Errors-in-variables equation discovery

Covered above: N26 (WENDy-MLE), N27 (modified SINDy), N28 (ODR-BINDy, already cited), N19 (PSI-SINDy, which treats
measurement error in the candidate terms). Further:

### N48. Fasel 2025, arXiv:2507.11739. "Sparse Identification of Nonlinear Dynamics with Conformal Prediction". **BACKGROUND**
- arXiv:2507.11739. Verified: ABSTRACT (API).
- What it says: conformal prediction with E-SINDy for forecast intervals, library feature importance and coefficient
  intervals, "even under non-Gaussian noise". A search snippet of the full text says SINDy's least squares ignores
  noise in the library inputs, which "would require solving an errors-in-variables problem".
- Why it matters: a coverage-guaranteed alternative to bootstrap intervals on coefficients.

**Negative result (EIV).** The arXiv query `abs:"errors-in-variables" AND (sparse OR SINDy OR "symbolic regression"
OR "equation discovery")` returned only `fung2026`/2507.23426 as an equation-discovery paper. No paper was found
that treats *error in a supplied constitutive function* (the measured isotherm) as the EIV regressor. H2c's framing
still looks new.

---

## 5. MOF / COF water-sorption kinetics, MOF-303 and step-isotherm kinetics

### N49. Lassitter, Hanikel, Coyle, ..., Yaghi & Glover 2024, Chem. Eng. Sci. 285:119430. "Mass transfer in atmospheric water harvesting systems". **MUST CITE** (primary source for H2d's k(q))
- DOI 10.1016/j.ces.2023.119430. Verified: FULL TEXT (PDF from the Yaghi group website). Passages found:
  - Concentration-swing frequency response (CSFR) on MOF-303, MOF-333 and 4/4-MTV-MOF. Fig. 4 caption: "The minimum
    in the diffusion rate is seen to correlate with the steep uptake step in the isotherm."
  - "the observed minimum in transport mobility is occurring not because of a large change in molecular mobility,
    but rather because of a significant change in the adsorption isotherm loading". The corrected (Maxwell-Stefan)
    diffusivity of MOF-303 is "fairly constant".
  - LDF-versus-micropore model: deviations appear "near ... 12 % for MOF-303 coinciding with the steep portion of the
    isotherms"; "the error associated with the LDF assumption is most prevalent where the isotherm is the steepest".
  - Against loading (Fig. 9b): "the minimum diffusion rate extends over a wide range of loadings".
  - A MOF-coated-tube model uses MOF-303 LDF coefficients from CSFR.
- Why it matters for Paper 2 (high priority):
  1. It is earlier and more direct than `abuelmaaty2024` for "the rate falls at the step", and it comes from Glover
     and Yaghi. Cite it first.
  2. It gives the *mechanism*: the drop is the Darken thermodynamic factor, D = D0 dlnp/dlnq, not a change in
     mobility. A discovery method that finds k(q) is rediscovering the isotherm slope. The physically natural
     discovery target is k proportional to (dq*/dp)^-1, a function of the isotherm, which Lib-B cannot express.
  3. Shape: the measured rate has a *minimum* at the step, and the minimum spans a wide loading range. L2 (a logistic
     drop to 0.2 k0 that stays low above the step) is monotone. That is a difference from the data to state in the
     limitations; the prereg is frozen.
  4. The LDF form itself is least accurate at the step. So at a MOF-303 step the "true law" is arguably not LDF,
     which matters for interpreting any H2d success.

### N50. Hastings, Lassitter, Zheng, Chheda, Siepmann, Gagliardi, Yaghi & Glover 2024, J. Phys. Chem. C 128:11328-11339. "High-Temperature Water Adsorption Isotherms and Ambient Temperature Water Diffusion Rates on Water Harvesting Metal-Organic Frameworks". **MUST CITE**
- DOI 10.1021/acs.jpcc.4c01733. Verified: FULL TEXT (PDF). Passages: water isotherms of MOF-303, MOF-LA2-1 and
  MIL-100(Fe) from 25 to 125 °C show "how the step in the water adsorption isotherm varies as a function of
  temperature". By CSFR, "micropore diffusion was identified as the controlling mechanism". "The Darken-predicted
  diffusion rate data show the expected dependence on loading, where diffusion slows at the step in the isotherm."
  This is "consistent with previously reported MOF303 diffusion data reported by Lassitter et al.". The paper also
  argues that frequency response is preferred to uptake (step) methods, which "fail to account for heat effects and
  system nonlinearities".
- Why it matters: (i) step position against temperature for MOF-303. The non-isothermal step case of Paper 2 depends
  on exactly this, and the paper should check its q*(c,T) step against these data. (ii) A second Glover/Yaghi source
  for "rate slows at the step". (iii) An argument that uptake-type data (like breakthrough) confound kinetics with
  heat effects, which supports the non-isothermal primary design.

### N51. Ma, Li, Guang, Li, Su & Zhou 2025, Nano Letters. "Microscopic Kinetics of Water Adsorption in Metal-Organic Frameworks". **MUST CITE**
- DOI 10.1021/acs.nanolett.5c00343. Verified: ABSTRACT (API). Found as a forward citation of Abu El-Maaty 2024.
- What it says: "At low relative humidities ... water molecules are adsorbed and diffuse freely ..., as described by
  the linear driving force assumption and Fick's law. At high RHs, water condenses into liquid clusters before
  diffusing, modeled by a two-concentration framework." It was validated on five MOFs, MOF-303 among them.
- Why it matters: the *form* of the rate law changes across the step (LDF below it, a two-concentration cluster model
  above it), not only its coefficient. This is a direct physical reason why H2d's "k(q) within an LDF form" is one of
  several possible targets. It is also a strong candidate for an L3 law in a future paper (paper series).

### N52. Bezrukov et al. 2023, Cell Reports Physical Science 4:101252. "Metal-organic frameworks as regeneration optimized sorbents for atmospheric water harvesting". **SHOULD CITE** (already in `research/lit_water_harvesting_twins.md` as S56, but not in the Paper 2 bibliography)
- DOI 10.1016/j.xcrp.2023.101252. Verified: ABSTRACT (API).
- What it says: "the AWH kinetics of seven known MOFs and the industry-standard desiccant Syloid are limited by
  diffusion to the sorbent bed surface". "A quantitative model that exploits isotherm shape" produces productivity
  "heatmaps". The dataset and code are open (Zenodo 10.5281/zenodo.6631710 and a GitHub repository; the code has no
  licence file, per the other review).
- Why it matters: (i) at bed scale, the rate-limiting step for MOF water uptake may be external or bed transport, not
  intracrystalline. A column-discovered "k" is then a lumped bed coefficient. (ii) Open raw uptake data on stepped
  MOFs is the only open dataset found for an experimental follow-up. (iii) Its "heatmaps" are a figure precedent for
  regime maps in this field.

### N53. Hanikel et al. 2021, Science. "Evolution of water structures in metal-organic frameworks for improved atmospheric water harvesting". **SHOULD CITE**
- DOI 10.1126/science.abj0890. Verified: ABSTRACT (API).
- What it says: in MOF-303, water first binds to polar linker sites, then forms isolated clusters, chains of clusters
  and finally a network. Multivariate (MTV) linkers tune the binding of the first water molecules and so "shap[e] the
  water uptake behavior".
- Why it matters: it is the molecular reason for the step, and so for a loading-dependent rate. It is the
  authoritative MOF-303 step reference for the Yaghi-facing goal.

### N54. Ben Mansour et al. 2025, Case Studies in Thermal Engineering. "Performance evaluation and cost analysis of MOF-303-based adsorption desalination and cooling systems using experimental dynamic data". **BACKGROUND**
- DOI 10.1016/j.csite.2025.107507. Verified: ABSTRACT (API).
- What it says: dynamic experiments on MOF-303 at regeneration temperatures of 40-80 °C, with "effective diffusion
  coefficients across different cycle times and operating conditions". The authors are the `abuelmaaty2024` group.
- Why it matters: more MOF-303 LDF-type kinetics fitted by hand.

### N55. Laurenz, Fuldner, Velte, Schnabel & Schmitz 2021, Int. J. Heat Mass Transfer 169:120921. "Frequency response analysis for the determination of thermal conductivity and water transport in MOF adsorbent coatings for heat transformation". **SHOULD CITE**
- DOI 10.1016/j.ijheatmasstransfer.2021.120921. Verified: METADATA (Crossref) plus abstract content through the TUHH
  repository page (paraphrased by the fetch tool). An aluminium fumarate (stepped) coating gives a diffusion time
  constant "which varies with loading and temperature". A search snippet of the same record mentions a U-shaped
  loading dependence.
- Why it matters: a second stepped water-MOF with a measured loading-dependent LDF/diffusion time constant.

### N56. Arjmandi & Mohamed 2026, ACS Applied Nano Materials. "Computational Prediction of the Complete Adsorption-Regeneration Cycle of Functionalized MOFs for Atmospheric Water Harvesting". **BACKGROUND**
- DOI 10.1021/acsanm.5c04879. Verified: ABSTRACT (API). Simulated Cu-functionalised MOF-303 kinetics, in which
  pristine MOF-303 "saturates in 4 min at 2000 Pa".

### N57. Li et al. 2025, Advanced Materials Interfaces. "Atmospheric Water Sorption Kinetics in Powder and Monolithic Metal-Organic Frameworks". **BACKGROUND**
- DOI 10.1002/admi.202400628. Verified: ABSTRACT (API). MOF-801 powder against monolith: capillary-condensation
  films in mesopores change the uptake kinetics. This shows that shaping changes the kinetic law, relevant to "MOF-303-like".

### N58. Shimizu & Matubayasi 2023, Langmuir. "Cooperativity in Sorption Isotherms". **BACKGROUND**
- DOI 10.1021/acs.langmuir.3c01243. Verified: ABSTRACT (API). A statistical-thermodynamic theory of sigmoidal
  (cooperative) isotherms. It is an alternative derivation of the step q* that the paper's "cooperative (Type V)"
  description could cite.

### N59. COF water kinetics. **Negative / weak.** The web search found the COF-309 / "hydrophilicity index" Yaghi-group
work (the ACS Central Science 2025 attribution comes from a search snippet; DOI not resolved, so not listed as
evidence) and a 2023 Angewandte DHTA-Pa COF rate report (snippet only). **No COF paper with a fitted rate law, LDF or
diffusion, at a water step was verified.** The MOF/COF symmetry of the project title is not supported on the kinetics
side. Say "MOF" in Paper 2 unless a COF kinetics source is read.

---

## 6. Scoop-risk search: has anyone mapped discovery success against a dimensionless group?

Searches: OpenAlex full text "SINDy Damkohler", "symbolic regression Damkohler number", "SINDy chromatography",
"equation discovery breakthrough curves", "sparse identification linear driving force", "equation discovery
identifiability profile likelihood"; arXiv `abs:"Damkohler" AND (machine learning OR sparse regression OR symbolic)`
(0 hits), `abs:SINDy AND abs:"Peclet"` (0 hits), `abs:"equation discovery" AND ("phase diagram" OR "regime map" OR
dimensionless)` (1 hit: N13); forward citations of Santana 2023 (26 citing works), Knox 2016 (58 since 2023) and
Abu El-Maaty 2024 (15). All lists were read.

**Verdict: no study found that maps rate-law discovery success against Da or Pe, or compares a discovery boundary
with an identifiability boundary on the same data.** Nearest items by risk:
1. **N11 Shumaylov et al. 2025 (moderate, conceptual).** It claims the general result that non-chaotic systems are not
   discoverable from trajectories alone. A referee could say Paper 2's failure at high Da is "expected from Shumaylov".
   Answer: Shumaylov is about uniqueness in function space with exact data. Paper 2 measures *where* finite-noise
   discovery fails, given priors (Lib-B), on a PDE, and compares this with parameter identifiability.
2. **N13 Lou et al. 2026 (low, wording).** It uses the phrase "phase diagram of equation discoverability", but with
   abstract axes (structural and coefficient complexity), not physics axes.
3. **N12 Loman, Browning & Baker 2026 and N29/N30 (low-moderate).** They pair discovery with identifiability, but
   structurally (differential algebra) or as a filter, with no boundary in a physical group.
4. **N14 Fajardo-Fontiveros 2023 (low).** A noise phase transition, for closed-form regression and not ODE/PDE rate laws.
5. **`taylor2026` (cited)** maps parameter sensitivity, not discovery, over Pe-Da.
6. **`gallo2026` (cited)** ties discoverability to trajectory geometry (moment-matrix eigenvalues). It is the closest
   mechanism paper, but has no adsorption content and no physical group.

The scoop risk for the paper's specific contribution is **low** as of 12 Oct 2026. The risk of a referee saying the
mechanism is known is **moderate** and rising (N11, N14, N15, `gallo2026`).

---

## 7. High-impact papers on the trustworthiness and limits of AI-discovered laws (what a Nature-family editor expects)

Must cite: N14 Fajardo-Fontiveros 2023 (Nat. Commun.). Should cite:
- **Cornelio et al. 2023, Nature Communications. "Combining data and theory for derivable scientific discovery with AI-Descartes".** DOI 10.1038/s41467-023-37236-y. Verified: ABSTRACT (API). It demonstrates on "Langmuir's theory of adsorption", and logical reasoning distinguishes "candidate formulae having similar error on the data". **Action: `cornelio2021` in stage1.tex cites the arXiv preprint; replace it with this Nat. Commun. version.**
- **Cory-Wright, Cornelio, Dash, El Khadir & Horesh 2024, Nature Communications 15:5922. "Evolving scientific discovery by unifying data and background knowledge with AI Hilbert".** DOI 10.1038/s41467-024-50074-w. Verified: ABSTRACT (Crossref). Derives laws "from axioms and experimental data" with certificates. It is the "theory-plus-data" route that Lib-B approximates.
- **Xie, Samaei, Guo, Liu & Gan 2022, Nature Communications. "Data-driven discovery of dimensionless numbers and governing laws from scarce measurements".** DOI 10.1038/s41467-022-35084-w. Verified: ABSTRACT (API). Discovers the dominant dimensionless groups *and* laws with dimensional invariance. It is relevant to the claim that R = delta/eps_eff is a dimensionless predictor chosen by hand. A referee may ask whether such a method would find R or Da. BACKGROUND to SHOULD CITE.
- **N24 Ruan et al. 2026 (Nat. Comput. Sci.)**, **N32 Aguilar et al. 2026 (PRX)**, **N2 Lamb et al. 2026 (Sci. Adv.)**, **N9 Kim & Deng 2024 (Nat. Commun.)**.
- **Vinuesa, ..., B. W. Brunton & S. L. Brunton 2026, Communications Physics. "Decoding complexity through machine learning is redefining scientific discovery" (Perspective).** DOI 10.1038/s42005-026-02676-7. Verified: ABSTRACT (API). It says reliance on ML "raises challenges for research practice and validation". It is general, so cite it at most in the opening.
- Not found: a 2024-2026 Nature, Science, Nature Reviews Physics or Nature Machine Intelligence piece *specifically* on the limits of AI-discovered physical laws (web search; not proof of absence). Shumaylov (N11) is the nearest, and it is a preprint.

---

# Implications for Paper 2

Ordered by priority. Paragraphs of stage1.tex are named by their subsection headings.

## A. Missing citations (add these)

**Priority 1 (a referee would flag their absence):**
1. **Lassitter et al. 2024 (N49) and Hastings et al. 2024 (N50)** in "Prior equation discovery for adsorption", MOF
   paragraph, and in H2d. They are the primary MOF-303 measurements of a rate minimum at the step, with a Darken
   explanation, from Glover and Yaghi.
2. **Shumaylov et al. 2025 (N11)** in "What is known and what is not new", generic-failure paragraph, next to
   `kaptanoglu2023`.
3. **Fajardo-Fontiveros et al. 2023 (N14)**: same paragraph. It is the Nat. Commun. learnability phase transition.
4. **Messenger & Bortz 2024 (N15)**: same paragraph, and in M2. It gives a proved noise threshold sigma_c for weak SINDy.
5. **Buchner & Pini 2026 (N41)** (plus Joss & Pini 2017) where O1 is introduced ("O1 is the optimistic ceiling").
6. **Wang & Dowling 2022, Pyomo.DOE (N37)** in "What is known" (adsorption engineering) and in §Identifiability.
7. **Ma et al. 2025 (N51)** in the MOF paragraph and the H2d limitations.
8. **Loman, Browning & Baker 2026 (N12)** next to `loman2025`.
9. **Replace `cornelio2021` (arXiv) with the Nat. Commun. 2023 version** (DOI 10.1038/s41467-023-37236-y).

**Priority 2:**
10. Canzano et al. 2012 (N44), the classical adsorption precedent: near-equilibrium data mislead rate-law selection.
11. N8 (SISR, SINDy prunes slow processes), next to `prabhu2025`/`huang2021`.
12. N26 WENDy-MLE, N27 modified SINDy, N19 PSI-SINDy, where EIV methods are listed ("Errors-in-variables
    equation-discovery methods \citep{fung2026,bortz2023}").
13. N18 BINDy and N17 Gao et al. at M3. N21 ODEBench and N22 SRBench 2.0 at "Methods compared".
14. N13 Lou et al. 2026 at the Aims ("The aim is a map ...") to position the map. N29/N30 (discovery plus
    identifiability) at "What this study adds".
15. N1 (OED for missing physics), N2 (Sci. Adv. UDE+SR success), N5 (Bayesian PINN non-identifiability on columns),
    N6 (2026 review on outlet-only equifinality), N39 DeJaco & Kearsley (high-Da asymptotics with inflected isotherms),
    N52 Bezrukov (bed-surface-limited MOF water kinetics), N53 Hanikel 2021 Science.
16. Before submission, read N38 (DeJaco et al. 2025, CES) in full before citing it. The `fung2026` DOI was checked
    and is correct (N28).

## B. Claims in the Introduction that the new literature contradicts or weakens

1. "Water uptake on MOF-303 has been fitted with an LDF model by hand, and the specific diffusion rate falls markedly
   where the isotherm inflects \citep{abuelmaaty2024}."
   - **Weakened (attribution and mechanism).** The stronger and earlier evidence is CSFR by Lassitter 2024 and
     Hastings 2024. They show the drop is a *minimum* at the step, explained by the Darken isotherm-slope factor with
     an almost constant corrected diffusivity. Rewrite, for example: "... the transport diffusivity of water in
     MOF-303 passes through a minimum at the isotherm step [Lassitter, Hastings], which the Darken relation attributes
     to the isotherm slope rather than to a change in molecular mobility; an LDF fit by hand shows the same fall
     [abuelmaaty2024]."
2. "A loading-dependent $k(q)$ at an isotherm step is an untested discovery target."
   - **Still true as a discovery claim, but needs qualification.** (a) The physics of k(q) is known (Darken). (b) The
     LDF form itself is least accurate at the step (Lassitter: "the error associated with the LDF assumption is most
     prevalent where the isotherm is the steepest"). (c) Above the step the rate law changes form (Ma 2025). (d) L2's
     monotone logistic drop differs from the measured minimum. State (b)-(d) in Design limitations. H2d remains a test
     of whether a *stylised* k(q) is discoverable, not of MOF-303's real law.
3. "One benchmark points the other way: on attractor-filling chaotic data, SINDy performance showed no significant
   dependence on scale separation \citep{kaptanoglu2023}."
   - **Should be reframed, not dropped.** Shumaylov et al. (N11) argue that chaotic benchmarks are exactly the
     discoverable case and that their prevalence "may have inadvertently obscured" the limitation. The sentence then
     becomes supporting context: the counter-evidence comes from the regime theory says is easiest.
4. "Nobody knows in which regimes such discovery works" (Abstract) and "This supports, but does not prove, that the
   regime question is open."
   - **Holds for adsorption, but the general question is no longer untouched.** Generic theory now exists (N11, N12,
     N14, N15, `gallo2026`). Rephrase the Abstract to "For adsorption, nobody has mapped ..." and add one sentence that
     general theory predicts failure for stable, equilibrating systems without priors, but cannot say where for a
     column with noise and isotherm error.
5. "The first is a quantitative discoverability boundary for the strongest available discovery methods" ("What this
   study adds").
   - **Exposed on "strongest available".** BINDy (Proc R Soc A 2025), WENDy-MLE (Julia, maintained), PSE (Nat Comput
     Sci 2026), and probabilistic symbolic regression (the Bayesian machine scientist, shown optimal in N14) are not
     in the comparison. Suggested wording: "the strongest methods we could run in their published configuration on
     this machine". Section C below lists them.
6. "Errors-in-variables equation-discovery methods \citep{fung2026,bortz2023} will be reported on their own published
   examples."
   - **Weakened for WENDy.** A Julia implementation with MLE now exists (N26), and the project already has an isolated
     Julia environment. Reporting WENDy as NOT RUN will be hard to defend unless WENDy.jl fails its own example.
     Recommendation: run WENDy.jl on its published example. If it passes, report it on its examples, as already
     promised for ODR-BINDy.
7. "O1 is the optimistic ceiling. O2 and O3 are where the experimentally realistic answer lies." (Methods)
   - **Partly contradicted, in the paper's favour.** Interior adsorbed-phase imaging during breakthrough exists (N41).
     Say O1 is "measurable with X-ray CT in specialised set-ups [Buchner & Pini 2026]", not merely hypothetical.

## C. Competitors or methods missing from the comparison

The design is frozen. Each item says whether it can enter as a *labelled exploratory* addition (allowed under the
paper's own rules if declared as an amendment before it runs) or should be named in Design limitations.
1. **Probabilistic / Bayesian-machine-scientist symbolic regression** (N14, N33). Highest editor expectation, because
   Fajardo-Fontiveros show it is optimal in the learnable phase. At minimum, name it as not run and say why. If it
   is feasible, run it on M7's subgrid.
2. **BINDy (RJ-MCMC)** (N18) as the strongest Bayesian SINDy. M3 is bagged STLSQ, while the text cites `hirsh2021`.
   Either run BINDy on a subgrid or relabel M3 honestly as "ensemble SINDy (E-SINDy)" and list Bayesian SINDy as not run.
3. **WENDy-MLE / WENDy.jl** (N26), on its published example (see B6).
4. **PSE** (N24), a Nat Comput Sci 2026 symbolic-regression method claiming large gains over PySR-class baselines.
   Name it in limitations.
5. **ODEFormer** (N21). A pre-trained transformer, cheap at inference. It cannot use `q*_meas` naturally, so it would
   be a Lib-A-like agnostic baseline. It is optional.
6. **Modified SINDy (AD-denoising)** (N27) as a third EIV-family method in limitations.
7. **Fisher-information (FIM) identifiability** (N37) as a cheap second identifiability measure alongside the
   profile likelihood, especially for O2/O3, where the profile has only 3 replicates. Report it descriptively.

## D. Design or analysis elements the field now expects

1. **A standard-benchmark sanity check.** Report each discovery method's recovery rate on a small ODEBench subset (N21),
   or at least on the systems used in `kaptanoglu2023`, with the same settings as on the grid. This shows that the
   implementations are not handicapped (the "straw man" risk). It fits the paper's existing known-answer-test
   culture and costs little.
2. **Metrics the field uses besides exact support.** Add, descriptively: true-positive rate / false-discovery counts
   (WSINDy and PDE-FIND style), *symbolic accuracy* (SRBench, LLM-SRBench), and held-out prediction error (NMSE).
   Exact support plus sign plus ratio stays primary, but a reader should see that partial recoveries (for example
   {q*_meas, q, c}) are counted.
3. **The theoretical noise threshold.** Where possible, compute or bound Messenger-Bortz's sigma_c (N15) for M2 on the
   Lib-B library and overlay it on the measured sigma boundary. Even "the bound is not computable for our library"
   is worth one sentence.
4. **Post-selection inference.** Frame amendment A1 (separate selection and estimation replicates) as the
   replicate-level counterpart of PSI-SINDy's data thinning (N19). This turns an amendment into a recognised practice.
5. **Calibration of uncertainty, not only its size.** For M3 inclusion probabilities, report calibration (does an
   inclusion probability of 0.9 mean 90 % correct?), as N17, N18 and N33 encourage. Report it descriptively.
6. **Functional identifiability check for H2d.** Use N12's framework to state whether k(q) is structurally
   functionally identifiable from O1/O2/O3 before reading H2d rates. A one-paragraph argument is enough.
7. **Check against MOF-303 data.** Compare the step isotherm's position and temperature shift with Hastings 2024
   (N50), and state the k(q) shape difference from Lassitter 2024 (N49) in Design limitations.

## E. Figure ideas used in this space

1. **A phase diagram with a learnable/unlearnable boundary** (Fajardo-Fontiveros N14; Lou et al. N13; Klishin et al.,
   cited). Plot P(success) as a heat map over (log10 Da, sigma) for each observation model, with the 50 % contour for
   discovery (solid) and for identifiability (dashed) on the *same* axes. That single panel shows H2b's three verdicts
   geometrically. It could become the main figure of Stage 2.
2. **Collapse plot for H2a.** P(success) against log10 R, with all slices overlaid in thin lines, the logistic fits,
   and a band marking the R* spread. This is the standard "data collapse" figure of statistical physics, which is also
   the language of N14.
3. **Rate against loading overlaid on the isotherm** (as in Lassitter Fig. 4/5 and Hastings Fig. 8). For H2d, plot the
   true k(q), the discovered k-hat(q) bins and q*(RH) on twin axes, so the reader sees that the drop sits at the step.
4. **Productivity-style contour "heatmaps"** (Bezrukov N52) are familiar to the MOF water-harvesting audience. Use the
   same visual grammar for the (Da, Pe) map at fixed sigma and epsilon.
5. **Inclusion-probability matrices.** Library terms (rows) against Da (columns), coloured by E-SINDy or BINDy
   inclusion probability. They show *how* discovery fails (which spurious term enters: c, q^2, or q*_meas alone), as
   in E-SINDy and BINDy papers.
6. **Gram-matrix conditioning against Da**, with the success boundary marked. This displays the paper's mechanistic
   predictor in the style of `gallo2026` and `delgado2025`.

## Top actions (summary)
1. Cite Lassitter 2024 and Hastings 2024, and rewrite the MOF-303 sentence and H2d limitations (Darken mechanism; a
   minimum, not a monotone drop; LDF least accurate at the step).
2. Add Shumaylov 2025, Fajardo-Fontiveros 2023 and Messenger & Bortz 2024 to "What is known", and reframe the
   `kaptanoglu2023` counter-evidence.
3. Qualify "strongest available methods": name the probabilistic symbolic regression, BINDy, WENDy-MLE and PSE that
   were not run, and run WENDy.jl on its own example rather than declaring it NOT RUN.
4. Cite Buchner & Pini 2026 to show that O1 interior loading is experimentally measurable, and Pyomo.DOE / FIM for
   the breakthrough-identifiability lineage.
5. Add descriptive standard metrics (TPR/false discoveries, symbolic accuracy, NMSE) and an ODEBench-subset sanity
   check. Plan the main Stage-2 figure as a shared-axes discovery and identifiability phase diagram.
