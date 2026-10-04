"""The bibliography, and a gate that refuses to emit an unverified reference.

Project rule 8: *nothing is cited until it has been FETCHED, not searched.* That rule
exists because the citation-verification pass itself once invented a co-author (B35),
and because a later pass put one paper's arXiv identifier on another paper named in
the same sentence (B42). Tranche 4 then found two references that do not contain the
claim they were cited for (B47, B53), a missing co-author (B52), and a correlation
attributed to the wrong source (B53).

So the bibliography is not hand-maintained. Every entry below carries:

    state   VERIFIED  the record was retrieved AND the claim we make was confirmed
            PARTIAL   the record is confirmed; the claim is NOT
            BLOCKED / UNRESOLVED
    via     for a PARTIAL, the verified secondary source the claim rests on
    note    the trap this entry exists to avoid, where there is one

**NEVER EXPAND AN INITIAL.** An author recorded as "E. Glueckauf" is written here as
"E. Glueckauf". Turning it into "Eugen Glueckauf" is an unverified assertion about a
real person's name, and it is exactly the B35 failure class -- a plausible name
component attached to a real paper. The first draft of this file expanded eleven
initials and invented a third author for a two-author paper (B62). Use the form the
verification pass actually recorded, or "and others".

**Only VERIFIED entries are written to references.bib.** A PARTIAL may be emitted
only when `allow_partial=True` is set on it explicitly, which means someone decided
that citing it through a named secondary source is honest -- and the note then says
which source. Anything else is refused, loudly.

    python paper/references.py            # write references.bib, report
    python paper/references.py --audit    # every entry, its state and its trap
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "paper", "references.bib")
TEX = os.path.join(ROOT, "paper", "manuscript.tex")

V, P = "VERIFIED", "PARTIAL"

# Where a fetched author string may be recorded. The given-name gate reads these.
PROVENANCE = [os.path.join("paper", "author_provenance.md"), "CITATIONS.md", os.path.join("audit_2026-08-30", "citation_verification.md")]

# For every PARTIAL emitted as citable: what the claim was actually read through.
# references.py writes these to paper/secondary_sources.tex, which the manuscript's
# reproducibility section \input's -- so the list the paper promises is generated
# from the same records that decide what is emitted, and cannot drift from them
# (audit_citations #1: the manuscript promised this list and did not contain it).
VIA = {
    "danckwerts1953continuous":
        r"the boundary conditions, read through Pearson~\cite{pearson1959note}",
    "glueckauf1955theory":
        r"the linear-driving-force factor, read through Perry's handbook~\cite{levan2019adsorption} "
        r"and Cruz, Magalh\~aes and Mendes, who attribute the plain factor to the companion "
        r"paper~\cite{glueckauf1947theory}, which is why both are cited",
    "klinkenberg1948numerical":
        r"the breakthrough approximation, read through Seader, Henley and Roper's "
        r"\emph{Separation Process Principles}, which attributes it to the later "
        r"paper~\cite{klinkenberg1954heat}; neither primary could be retrieved, so both are cited",
    "anzelius1926uber":
        r"the Anzelius--Schumann solution, read through Perry's handbook~\cite{levan2019adsorption}",
    "schumann1929heat":
        r"the Anzelius--Schumann solution, read through Perry's handbook~\cite{levan2019adsorption}",
    "dodo2000model":
        r"the two-term functional form, read through Buttersack~\cite{buttersack2019modeling}, "
        r"who proposes a competing isotherm",
}

# Verified records kept for their history but NOT emitted, because no sentence in the
# manuscript cites them (audit_citations #9). elsarticle-num drops an uncited entry
# silently anyway; excluding it here makes the decision visible and deliberate.
NOT_EMITTED = {
    "gowrachari2025cross": "no sentence in the manuscript needs it",
    "ohlberger2013nonlinear": "the 2016 companion carries the bound we state",
    "greif2019decay": "CITATIONS.md conditions it on wave problems being discussed; they are not",
}

# key, state, bibtex type, fields, note, allow_partial
REFS = [
    # ------------------------------------------------------------ operator learning
    ("lanthaler2023nonlinear", V, "inproceedings", dict(
        author="Samuel Lanthaler and Roberto Molinaro and Patrik Hadorn and Siddhartha Mishra",
        title="Nonlinear reconstruction for operator learning of {PDEs} with discontinuities",
        booktitle="International Conference on Learning Representations (ICLR)",
        year="2023", eprint="2210.01074", archiveprefix="arXiv"),
     "Proves the lower bound on linear-reconstruction operators and that FNO escapes it. "
     "This is why running FNO was not optional.", False),
    ("heinlein2026error", V, "article", dict(
        author="Alexander Heinlein and Johannes Taraz",
        title="The error of deep operator networks is the sum of its parts: branch--trunk and "
              "mode error decompositions",
        journal="arXiv preprint", year="2026", eprint="2602.21910", archiveprefix="arXiv"),
     "Partial priority on L5's mechanism. Cite prominently and differentiate on the four "
     "axes in CITATIONS.md.", False),
    ("bartolucci2023reno", V, "inproceedings", dict(
        author="Francesca Bartolucci and Emmanuel de B{\\'e}zenac and Bogdan Raoni{\\'c} and "
               "Roberto Molinaro and Siddhartha Mishra and Rima Alaifari",
        title="Representation equivalent neural operators: a framework for alias-free operator learning",
        booktitle="Advances in Neural Information Processing Systems (NeurIPS)",
        volume="36", year="2023", eprint="2305.19913", archiveprefix="arXiv"),
     "Six-author list checked character by character against arXiv, DBLP and the NeurIPS "
     "proceedings page. Diagnostic framework -- do NOT cite as a solved problem.", False),
    ("herde2024poseidon", V, "article", dict(
        author="Maximilian Herde and Bogdan Raoni{\\'c} and Tobias Rohner and Roger K{\\\"a}ppeli "
               "and Roberto Molinaro and Emmanuel de B{\\'e}zenac and Siddhartha Mishra",
        title="Poseidon: efficient foundation models for {PDEs}",
        journal="arXiv preprint", year="2024", eprint="2405.19101", archiveprefix="arXiv"),
     "B42: A23 originally carried MPP's identifier here. Poseidon is 2405.19101.", False),
    ("mccabe2023multiple", V, "article", dict(
        author="Michael McCabe and others",
        title="Multiple physics pretraining for physical surrogate models",
        journal="arXiv preprint", year="2023", eprint="2310.02994", archiveprefix="arXiv"),
     "The identifier A23 had attached to Poseidon.", False),
    ("krass2025mofsimbench", V, "article", dict(
        author="Kra{\\ss} and Huang and Moosavi",
        title="{MOFSimBench}: evaluating universal machine learning interatomic potentials in "
              "metal--organic framework molecular modeling",
        journal="npj Computational Materials", volume="12", pages="4", year="2025",
        doi="10.1038/s41524-025-01872-3"),
     "Held-out MATERIALS, but for interatomic potentials, not operator learning. Cite it "
     "as the falsifier of the broad novelty claim A23 withdrew.", False),

    # ------------------------------ material-as-input surrogates of adsorption (B68)
    # Found 2026-09-25 by the program literature pass (research/lit_water_harvesting_
    # twins.md S22, S23, S29). The introduction's novelty paragraph did not cite them;
    # MAPLE is the paper an adsorption-engineering referee would raise first.
    ("pai2020generalized", V, "article", dict(
        author="Kasturi Nagesh Pai and Vinay Prasad and Arvind Rajendran",
        title="Generalized, adsorbent-agnostic, artificial neural network framework for rapid "
              "simulation, optimization, and adsorbent screening of adsorption processes",
        journal="Industrial \\& Engineering Chemistry Research", volume="59", number="38",
        pages="16730--16740", year="2020", doi="10.1021/acs.iecr.0c02339"),
     "MAPLE: Langmuir isotherm parameters as INPUTS, cyclic-steady-state KPIs as outputs, "
     "'any arbitrary adsorbent'. Scalars at CSS, not transient fields; Langmuir only.", False),
    ("hesthaven2018non", V, "article", dict(
        author="J. S. Hesthaven and S. Ubbiali",
        title="Non-intrusive reduced order modeling of nonlinear problems using neural networks",
        journal="Journal of Computational Physics", volume="363", pages="55--78", year="2018",
        doi="10.1016/j.jcp.2018.02.037"),
     "POD basis plus a neural map from parameters to its coefficients (POD-NN): the class our "
     "L1 arms belong to (referee M10). Crossref record checked 2026-10-04.", False),
    ("subraveti2019machine", V, "article", dict(
        author="Sai Gokul Subraveti and Zukui Li and Vinay Prasad and Arvind Rajendran",
        title="Machine learning-based multiobjective optimization of pressure swing adsorption",
        journal="Industrial \\& Engineering Chemistry Research", volume="58", number="44",
        pages="20412--20422", year="2019", doi="10.1021/acs.iecr.9b04173"),
     "ML surrogate of a PSA process used for multiobjective optimisation (referee M10). Cited "
     "only for what its title states. Crossref record checked 2026-10-04.", False),
    ("burns2020prediction", V, "article", dict(
        author="Thomas D. Burns and Kasturi Nagesh Pai and Sai Gokul Subraveti and Sean P. Collins "
               "and Mykhaylo Krykunov and Arvind Rajendran and Tom K. Woo",
        title="Prediction of {MOF} performance in vacuum swing adsorption systems for postcombustion "
              "{CO$_2$} capture based on integrated molecular simulations, process optimizations, "
              "and machine learning models",
        journal="Environmental Science \\& Technology", volume="54", number="7", pages="4536--4544",
        year="2020", doi="10.1021/acs.est.9b07407"),
     "MOF screening at the process level with ML models (referee M10). Cited only for what its "
     "title states. Crossref record checked 2026-10-04.", False),
    ("leperi2019development", V, "article", dict(
        author="Karson T. Leperi and Yongchul G. Chung and Fengqi You and Randall Q. Snurr",
        title="Development of a general evaluation metric for rapid screening of adsorbent materials "
              "for postcombustion {CO$_2$} capture",
        journal="ACS Sustainable Chemistry \\& Engineering", volume="7", number="13",
        pages="11529--11539", year="2019", doi="10.1021/acssuschemeng.9b01418"),
     "Process-aware adsorbent screening (referee M10). Cited only for what its title states. "
     "Crossref record checked 2026-10-04.", False),
    ("hanikel2019rapid", V, "article", dict(
        author="Nikita Hanikel and Mathieu S. Pr{\\'e}vot and Farhad Fathieh and Eugene A. Kapustin and Hao Lyu and Haoze Wang and Nicolas J. Diercks and T. Grant Glover and Omar M. Yaghi",
        title="{Rapid Cycling and Exceptional Yield in a Metal-Organic Framework Water Harvester}",
        journal="ACS Central Science",
        volume="5",
        number="10",
        pages="1699--1706",
        year="2019",
        doi="10.1021/acscentsci.9b00745"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("fathieh2018practical", V, "article", dict(
        author="Farhad Fathieh and Markus J. Kalmutzki and Eugene A. Kapustin and Peter J. Waller and Jingjing Yang and Omar M. Yaghi",
        title="{Practical water production from desert air}",
        journal="Science Advances",
        volume="4",
        number="6",
        pages="eaat3198",
        year="2018",
        doi="10.1126/sciadv.aat3198"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("furukawa2014water", V, "article", dict(
        author="Hiroyasu Furukawa and Felipe G{\\'a}ndara and Yue-Biao Zhang and Juncong Jiang and Wendy L. Queen and Matthew R. Hudson and Omar M. Yaghi",
        title="{Water Adsorption in Porous Metal--Organic Frameworks and Related Materials}",
        journal="Journal of the American Chemical Society",
        volume="136",
        number="11",
        pages="4369--4381",
        year="2014",
        doi="10.1021/ja500330a"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("solovyeva2021cau", V, "article", dict(
        author="Marina V. Solovyeva and Alexandr I. Shkatulov and Larisa G. Gordeeva and Elizaveta A. Fedorova and Tamara A. Krieger and Yuri I. Aristov",
        title="{Water Vapor Adsorption on CAU-10- <i>X</i> : Effect of Functional Groups on Adsorption Equilibrium and Mechanisms}",
        journal="Langmuir",
        volume="37",
        number="2",
        pages="693--702",
        year="2021",
        doi="10.1021/acs.langmuir.0c02729"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("frohlich2016water", V, "article", dict(
        author="Dominik Fr{\\\"o}hlich and Evangelia Pantatosaki and Panagiotis D. Kolokathis and Karen Markey and Helge Reinsch and Max Baumgartner and Monique A. van der Veen and Dirk E. De Vos and Norbert Stock and George K. Papadopoulos and Stefan K. Henninger and Christoph Janiak",
        title="{Water adsorption behaviour of CAU-10-H: a thorough investigation of its structure--property relationships}",
        journal="Journal of Materials Chemistry A",
        volume="4",
        number="30",
        pages="11859--11869",
        year="2016",
        doi="10.1039/c6ta01757f"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("laurenz2020novel", V, "article", dict(
        author="Eric Laurenz and Gerrit F{\\\"u}ldner and Lena Schnabel and Gerhard Schmitz",
        title="{A Novel Approach for the Determination of Sorption Equilibria and Sorption Enthalpy Used for MOF Aluminium Fumarate with Water}",
        journal="Energies",
        volume="13",
        number="11",
        pages="3003",
        year="2020",
        doi="10.3390/en13113003"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("solovyeva2021mil", V, "article", dict(
        author="Marina Solovyeva and Irina Krivosheeva and Larisa Gordeeva and Yuri Aristov",
        title="{MIL-160 as an Adsorbent for Atmospheric Water Harvesting}",
        journal="Energies",
        volume="14",
        number="12",
        pages="3586",
        year="2021",
        doi="10.3390/en14123586"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("aumond2026adsorption", V, "article", dict(
        author="Thibaud Aumond and Micka{\\\"e}le Bonneau and C{\\'e}cile Daniel and Miriam Perbet and Francis Meunier and David Farrusseng",
        title="{Adsorption Performances of Water-Stable MIL-160(Al) at Scale: An Alternative to FAM-Z02 in Water Harvesting and Chillers}",
        journal="ACS Omega",
        volume="11",
        number="10",
        pages="16294--16299",
        year="2026",
        doi="10.1021/acsomega.5c11973"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("lenzen2019metal", V, "article", dict(
        author="Dirk Lenzen and Jingjing Zhao and Sebastian-Johannes Ernst and Mohammad Wahiduzzaman and A. Ken Inge and Dominik Fr{\\\"o}hlich and Hongyi Xu and Hans-J{\\\"o}rg Bart and Christoph Janiak and Stefan Henninger and Guillaume Maurin and Xiaodong Zou and Norbert Stock",
        title="{A metal--organic framework for efficient water-based ultra-low-temperature-driven cooling}",
        journal="Nature Communications",
        volume="10",
        number="1",
        pages="3025",
        year="2019",
        doi="10.1038/s41467-019-10960-0"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("rieth2017record", V, "article", dict(
        author="Adam J. Rieth and Sungwoo Yang and Evelyn N. Wang and Mircea Dinc{\\u{a}}",
        title="{Record Atmospheric Fresh Water Capture and Heat Transfer with a Material Operating at the Water Uptake Reversibility Limit}",
        journal="ACS Central Science",
        volume="3",
        number="6",
        pages="668--672",
        year="2017",
        doi="10.1021/acscentsci.7b00186"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("pai2022experimental", V, "article", dict(
        author="Kasturi Nagesh Pai and Tai T. T. Nguyen and Vinay Prasad and Arvind Rajendran",
        title="Experimental validation of an adsorbent-agnostic artificial neural network "
              "({ANN}) framework for the design and optimization of cyclic adsorption processes",
        journal="Separation and Purification Technology", volume="290", pages="120783",
        year="2022", doi="10.1016/j.seppur.2022.120783"),
     "Measured N2/O2 isotherms of 13X and LiX 'were not a part of the dataset used to train "
     "the model'; rig error 3/5/9 %. Material transfer at the KPI level IS established.", False),
    ("ceccanti2026deep", V, "article", dict(
        author="Beatrice Ceccanti and Mattia Galanti and Ivo Roghair and Martin van Sint Annaland",
        title="Deep operator networks for surrogate modeling of cyclic adsorption processes "
              "with varying initial conditions",
        journal="arXiv preprint", year="2026", eprint="2601.09491", archiveprefix="arXiv"),
     "Operator learning on TVSA; its out-of-distribution axis is INITIAL CONDITIONS, not "
     "materials. Isothermal per the program review.", False),

    # --------------------------------------------- the L4 weighting schemes (audit #6)
    # VERIFIED in CITATIONS.md since tranche 1 and named in PREREG_L4b_v2.md against the
    # arm each implements, but never carried into this file -- so the manuscript named
    # four methods from the literature and could cite none of them.
    ("wang2021understanding", V, "article", dict(
        author="Sifan Wang and Yujun Teng and Paris Perdikaris",
        title="Understanding and mitigating gradient flow pathologies in physics-informed "
              "neural networks",
        journal="SIAM Journal on Scientific Computing", volume="43", number="5",
        pages="A3055--A3081", year="2021", doi="10.1137/20M1318043"),
     "The gradient-norm balancing arm.", False),
    ("wang2022when", V, "article", dict(
        author="Sifan Wang and Xinling Yu and Paris Perdikaris",
        title="When and why {PINNs} fail to train: a neural tangent kernel perspective",
        journal="Journal of Computational Physics", volume="449", pages="110768", year="2022",
        doi="10.1016/j.jcp.2021.110768"),
     "The NTK arm. Ours uses per-point gradient norms as a trace estimate, EMA-smoothed -- a "
     "stated approximation, not their eigen-decomposition.", False),
    ("romano2005stepwise", V, "article", dict(
        author="Joseph P. Romano and Michael Wolf",
        title="Stepwise multiple testing as formalized data snooping",
        journal="Econometrica", volume="73", number="4", pages="1237--1282", year="2005",
        doi="10.1111/j.1468-0262.2005.00615.x"),
     "The studentised max-statistic bootstrap for a best-of-K comparison chosen after "
     "looking (referee M3, selection_adjust.py). Record checked against Crossref "
     "2026-10-04. The single-step simultaneous interval we use is the first step of "
     "their stepdown procedure.", False),
    ("mcclenny2023self", V, "article", dict(
        author="Levi D. McClenny and Ulisses M. Braga-Neto",
        title="Self-adaptive physics-informed neural networks",
        journal="Journal of Computational Physics", volume="474", pages="111722", year="2023",
        doi="10.1016/j.jcp.2022.111722"),
     "The self-adaptive arm. The JOURNAL title (Crossref) drops the arXiv title's "
     "'using a soft attention mechanism' -- do not copy the arXiv title.", False),
    ("rathore2024challenges", V, "inproceedings", dict(
        author="Rathore and Lei and Frangella and Lu and Udell",
        title="Challenges in training {PINNs}: a loss landscape perspective",
        booktitle="International Conference on Machine Learning (ICML)", year="2024",
        eprint="2402.01868", archiveprefix="arXiv"),
     "The Adam-then-L-BFGS polish (Q4). Surnames only until the arXiv record is fetched "
     "into author_provenance.md -- rule 11.", False),

    # -------------------------------------------------------- the critique literature
    ("mcgreivy2024weak", V, "article", dict(
        author="Nick McGreivy and Ammar Hakim",
        title="Weak baselines and reporting biases lead to overoptimism in machine learning "
              "for fluid-related partial differential equations",
        journal="Nature Machine Intelligence", volume="6", number="10", pages="1256--1269",
        year="2024", doi="10.1038/s42256-024-00897-5"),
     "The 79 % (60/76) denominator is articles that solve a fluid-related PDE AND claim to "
     "beat a standard numerical method. Do not widen it, and do not attach it to the "
     "reporting-bias half, which is qualitative.", False),
    ("grossmann2024pinn", V, "article", dict(
        author="Tamara G. Grossmann and Urszula Julia Komorowska and Jonas Latz and "
               "Carola-Bibiane Sch{\\\"o}nlieb",
        title="Can physics-informed neural networks beat the finite element method?",
        journal="IMA Journal of Applied Mathematics", volume="89", number="1",
        pages="143--174", year="2024", doi="10.1093/imamat/hxae011"),
     "The finding is explicitly 'in our study', on low-dimensional FEM-friendly problems. "
     "The abstract also concedes the networks were faster to evaluate.", False),
    ("rohrer2021loss", V, "article", dict(
        author="Rohrer and Tierney and Uhlmann and others",
        title="Putting the self in self-correction: findings from the Loss-of-Confidence Project",
        journal="Perspectives on Psychological Science", volume="16", number="6",
        pages="1255--1269", year="2021", doi="10.1177/1745691620964106"), "", False),

    # ------------------------------------------------------------- the KAN cluster
    ("abueidda2025deepokan", V, "article", dict(
        author="Diab W. Abueidda and Panos Pantidis and Mostafa E. Mobasher",
        title="{DeepOKAN}: deep operator network based on {Kolmogorov--Arnold} networks for "
              "mechanics problems",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="436",
        pages="117699", year="2025", doi="10.1016/j.cma.2024.117699"),
     "DOI year segment is 2024, not 2025. Their DeepOKAN is NOT physics-informed (B45) -- "
     "it pre-empts the name and the Gaussian-RBF basis only.", False),
    ("shukla2024comprehensive", V, "article", dict(
        author="Khemraj Shukla and Juan Diego Toscano and Zhicheng Wang and Zongren Zou and "
               "George Em Karniadakis",
        title="A comprehensive and {FAIR} comparison between {MLP} and {KAN} representations "
              "for differential equations and operator networks",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="431",
        pages="117290", year="2024", doi="10.1016/j.cma.2024.117290"),
     "Their conclusion is two-tiered, not 'MLPs beat KANs'. They DO build physics-informed "
     "DeepOKANs, so they are the prior art for that, not Abueidda.", False),
    ("wang2025kinn", V, "article", dict(
        author="Yizheng Wang and Jia Sun and Jinshuai Bai and Cosmin Anitescu and "
               "Mohammad Sadegh Eshaghi and Xiaoying Zhuang and Timon Rabczuk and Yinghua Liu",
        title="{Kolmogorov--Arnold}-informed neural network: a physics-informed deep learning "
              "framework for solving forward and inverse problems based on {Kolmogorov--Arnold} networks",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="433",
        pages="117518", year="2025", doi="10.1016/j.cma.2024.117518"),
     "DOI year segment is 2024. EIGHT authors. This paper CUTS AGAINST us -- KINN beats MLP "
     "-- and must be cited as part of a split literature (B46).", False),
    ("kiyani2025optimizing", V, "article", dict(
        author="Elham Kiyani and Khemraj Shukla and Jorge F. Urb{\\'a}n and J{\\'e}r{\\^o}me "
               "Darbon and George Em Karniadakis",
        title="Optimizing the optimizer for physics-informed neural networks and "
              "{Kolmogorov--Arnold} networks",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="446",
        pages="118308", year="2025", doi="10.1016/j.cma.2025.118308"),
     "Does NOT say KANs need a different optimiser -- it says BOTH improve under the same "
     "self-scaled quasi-Newton schemes (B46).", False),
    ("rigas2026training", V, "article", dict(
        author="Spyros Rigas and Fotios Anagnostopoulos and Michalis Papachristou and "
               "Georgios Alexandridis",
        title="Training deep physics-informed {Kolmogorov--Arnold} networks",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="452",
        pages="118761", year="2026", doi="10.1016/j.cma.2026.118761"),
     "Year is 2026 (Semantic Scholar says 2025). About initialisation and architecture, NOT "
     "optimisers. An SSRN preprint carries a different title.", False),

    # ------------------------------------------- reduced order models, registration
    ("reiss2018shifted", V, "article", dict(
        author="Julius Reiss and Philipp Schulze and J{\\\"o}rn Sesterhenn and Volker Mehrmann",
        title="The shifted proper orthogonal decomposition: a mode decomposition for multiple "
              "transport phenomena",
        journal="SIAM Journal on Scientific Computing", volume="40", number="3",
        pages="A1322--A1344", year="2018", doi="10.1137/17M1140571"),
     "B35: the fourth author is MEHRMANN, not Noack. Umlaut on Joern. Year 2018, not the "
     "2015 arXiv date Semantic Scholar reports.", False),
    ("krah2025robust", V, "article", dict(
        author="Philipp Krah and Arthur Marmin and Beata Zorawski and Julius Reiss and Kai Schneider",
        title="A robust shifted proper orthogonal decomposition: proximal methods for "
              "decomposing flows with multiple transports",
        journal="SIAM Journal on Scientific Computing", volume="47", number="2",
        pages="A633--A656", year="2025", doi="10.1137/24M164392X"),
     "DOI ends in the letter X and is one character from the Taddei erratum's. Do not transpose.",
     False),
    ("krah2023front", V, "article", dict(
        author="Philipp Krah and Steffen B{\\\"u}chholz and Matthias H{\\\"a}ringer and Julius Reiss",
        title="Front transport reduction for complex moving fronts",
        journal="Journal of Scientific Computing", volume="96", number="1", pages="28",
        year="2023", doi="10.1007/s10915-023-02210-9"),
     "B50: a COMPOSITIONAL construction from inside the sPOD school, so 'sPOD is additive, "
     "ours is compositional' is too clean a distinction.", False),
    ("zorawski2024neural", V, "article", dict(
        author="Beata Zorawski and Shubhaditya Burela and Philipp Krah and Arthur Marmin and "
               "Kai Schneider",
        title="Automated transport separation using the neural shifted proper orthogonal decomposition",
        journal="arXiv preprint", year="2024", eprint="2407.17539", archiveprefix="arXiv"),
     "B48: do NOT copy arXiv's Related DOI -- it belongs to a different paper. Burela was "
     "missing from our list. Proceedings not peer-reviewed.", False),
    ("papapicco2022nnspod", V, "article", dict(
        author="Davide Papapicco and Nicola Demo and Michele Girfoglio and Giovanni Stabile "
               "and Gianluigi Rozza",
        title="The neural network shifted-proper orthogonal decomposition: a machine learning "
              "approach for non-linear reduction of hyperbolic equations",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="392",
        pages="114687", year="2022", doi="10.1016/j.cma.2022.114687"),
     "PRIORITY FLAG: predates Zorawski by two years, so 'the neural sPOD' is not theirs. "
     "Fetched directly from Crossref works/10.1016/j.cma.2022.114687 on 2026-09-28: vol. 392, "
     "art. 114687, March 2022, the five authors above. Cited only for its existence and "
     "date (audit_citations #13).", False),
    ("taddei2020registration", V, "article", dict(
        author="Tommaso Taddei",
        title="A registration method for model order reduction: data compression and geometry reduction",
        journal="SIAM Journal on Scientific Computing", volume="42", number="2",
        pages="A997--A1027", year="2020", doi="10.1137/19M1271270"),
     "It is a parameter-INDEPENDENT method that PRODUCES a parameter-dependent map. Cite "
     "the erratum alongside.", False),
    ("taddei2026erratum", V, "article", dict(
        author="Tommaso Taddei",
        title="Erratum: A registration method for model order reduction: data compression and "
              "geometry reduction",
        journal="SIAM Journal on Scientific Computing", volume="48", number="3",
        pages="A1839--A1842", year="2026", doi="10.1137/24M1639579"), "", False),
    ("zucatti2026model", V, "article", dict(
        author="Victor Zucatti and Matthew J. Zahr",
        title="Model reduction of convection-dominated viscous conservation laws using implicit "
              "feature tracking and landmark image registration",
        journal="Journal of Computational Physics", volume="561", pages="114958", year="2026",
        doi="10.1016/j.jcp.2026.114958"),
     "B49: PUBLISHED since tranche 3 -- citing it as a preprint would be a defect. This is "
     "the NEAREST PRIOR ART and section 7 must name it.", False),
    ("nair2019transported", V, "article", dict(
        author="Nirmal J. Nair and Maciej Balajewicz",
        title="Transported snapshot model order reduction approach for parametric, steady-state "
              "fluid flows containing parameter-dependent shocks",
        journal="International Journal for Numerical Methods in Engineering", volume="117",
        number="12", pages="1234--1262", year="2019", doi="10.1002/nme.5998"), "", False),
    ("mendible2020dimensionality", V, "article", dict(
        author="Ariana Mendible and Steven L. Brunton and Aleksandr Y. Aravkin and Wes Lowrie "
               "and J. Nathan Kutz",
        title="Dimensionality reduction and reduced-order modeling for traveling wave physics",
        journal="Theoretical and Computational Fluid Dynamics", volume="34", number="4",
        pages="385--400", year="2020", doi="10.1007/s00162-020-00529-9"), "", False),
    ("gowrachari2025cross", V, "article", dict(
        author="Harshith Gowrachari and Giovanni Stabile and Gianluigi Rozza",
        title="Model reduction for transport-dominated problems via cross-correlation based "
              "snapshot registration",
        journal="arXiv preprint", year="2025", eprint="2501.01299", archiveprefix="arXiv"),
     "A NEGATIVE result in our favour: registration ROM has not been taken into "
     "separation-process column fields. A search summary claimed otherwise and was wrong.",
     False),
    ("ohlberger2016reduced", V, "inproceedings", dict(
        author="Mario Ohlberger and Stephan Rave",
        title="Reduced basis methods: success, limitations and future challenges",
        booktitle="Proceedings of ALGORITMY", pages="1--12", year="2016",
        eprint="1511.02021", archiveprefix="arXiv"),
     "B47: THIS is the slow-n-width citation, not their 2013 paper. It proves a LOWER bound "
     "d_N >= (1/2) N^-1/2 -- write 'decays no faster than', never 'decays like'.", False),
    ("ohlberger2013nonlinear", V, "article", dict(
        author="Mario Ohlberger and Stephan Rave",
        title="Nonlinear reduced basis approximation of parameterized evolution equations via "
              "the method of freezing",
        journal="Comptes Rendus Math{\\'e}matique", volume="351", number="23--24",
        pages="901--906", year="2013", doi="10.1016/j.crma.2013.10.028"),
     "B47: does NOT contain the n-width claim -- the words 'Kolmogorov' and 'n-width' appear "
     "nowhere in it. Cite ONLY for nonlinear/freezing transformations.", False),
    ("greif2019decay", V, "article", dict(
        author="Constantin Greif and Karsten Urban",
        title="Decay of the {Kolmogorov} {N}-width for wave problems",
        journal="Applied Mathematics Letters", volume="96", pages="216--222", year="2019",
        doi="10.1016/j.aml.2019.05.013"),
     "For the WAVE equation, not linear transport. A companion, not a substitute.", False),
    ("kneip1992statistical", V, "article", dict(
        author="Alois Kneip and Theo Gasser",
        title="Statistical tools to analyze data representing a sample of curves",
        journal="The Annals of Statistics", volume="20", number="3", year="1992",
        doi="10.1214/aos/1176348769"),
     "B38: the correct LANDMARK-registration ancestor.", False),
    ("ramsay1998curve", V, "article", dict(
        author="J. O. Ramsay and Xiaochun Li", title="Curve registration",
        journal="Journal of the Royal Statistical Society: Series B", volume="60",
        number="2", pages="351--363", year="1998", doi="10.1111/1467-9868.00129"),
     "DOI trap: ...00115 is a DIFFERENT JRSS-B 1998 paper. The landmark-FREE branch, cited "
     "as the canonical curve-registration reference and as the contrast.", False),

    # ------------------------------------------------------- adsorption and transport
    ("vangenuchten1982analytical", V, "techreport", dict(
        author="M. Th. van Genuchten and W. J. Alves",
        title="Analytical solutions of the one-dimensional convective-dispersive solute "
              "transport equation",
        institution="U.S. Department of Agriculture, Agricultural Research Service",
        number="Technical Bulletin 1661", year="1982"),
     "B10/B59: defines the third- or FLUX-type inlet [9b] and cites Ogata & Banks for the "
     "first-type. It never uses the name 'Danckwerts'. It also states that the flux-type "
     "condition conserves mass where the concentration-type does not -- which is B8.", False),
    ("ogata1961solution", V, "techreport", dict(
        author="Akio Ogata and R. B. Banks",
        title="A solution of the differential equation of longitudinal dispersion in porous media",
        institution="U.S. Geological Survey", number="Professional Paper 411-A",
        pages="A1--A7", year="1961"),
     "Pages are A1--A7; van Genuchten & Alves cite A1--A9, which is THEIR error. First-type "
     "inlet -- the reference our L0 originally used by mistake.", False),
    ("pearson1959note", V, "article", dict(
        author="J. R. A. Pearson",
        title="A note on the ``{Danckwerts}'' boundary conditions for continuous flow reactors",
        journal="Chemical Engineering Science", volume="10", number="4", pages="281--284",
        year="1959", doi="10.1016/0009-2509(59)80063-4"),
     "The scare quotes are part of the published title. Cite for the standing of the "
     "boundary conditions, since Danckwerts 1953 could not be read.", False),
    ("danckwerts1953continuous", P, "article", dict(
        author="P. V. Danckwerts",
        title="Continuous flow systems: distribution of residence times",
        journal="Chemical Engineering Science", volume="2", number="1", pages="1--13",
        year="1953", doi="10.1016/0009-2509(53)80001-1"),
     "B58: closed, no abstract anywhere -- the boundary-condition statement was NOT read "
     "from it. Cited through Pearson (1959). Crossref DROPS the subtitle; it is restored "
     "here by hand. Langmuir obtained the same solution in 1908.", True),
    ("glueckauf1955theory", P, "article", dict(
        author="E. Glueckauf",
        title="Theory of chromatography. {Part} 10.---{Formul{\\ae}} for diffusion into spheres "
              "and their application to chromatography",
        journal="Transactions of the Faraday Society", volume="51", pages="1540--1551",
        year="1955", doi="10.1039/TF9555101540"),
     "B55: BLOCKED at the primary. The factor 15 is attributed by Cruz et al. to Glueckauf & "
     "Coates (1947); the 1955 result carries an extra term. Cite both.", True),
    ("glueckauf1947theory", V, "article", dict(
        author="E. Glueckauf and J. I. Coates",
        title="Theory of chromatography. {Part} {IV}. The influence of incomplete equilibrium "
              "on the front boundary of chromatograms and on the effectiveness of separation",
        journal="Journal of the Chemical Society", pages="1315", year="1947",
        doi="10.1039/jr9470001315"),
     "Coates is the co-author most often dropped -- B35's failure mode.", False),
    ("klinkenberg1948numerical", P, "article", dict(
        author="Adriaan Klinkenberg",
        title="Numerical evaluation of equations describing transient heat and mass transfer "
              "in packed solids",
        journal="Industrial \\& Engineering Chemistry", volume="40", number="10",
        pages="1992--1994", year="1948", doi="10.1021/ie50466a034"),
     "B54, OPEN: Seader, Henley & Roper attribute L7's erf expression to Klinkenberg 1954, "
     "not this paper. Neither is retrievable. Cite BOTH years until one is read.", True),
    ("klinkenberg1954heat", V, "article", dict(
        author="Adriaan Klinkenberg",
        title="Heat transfer in cross-flow heat exchangers and packed beds",
        journal="Industrial \\& Engineering Chemistry", volume="46", number="11",
        pages="2285--2289", year="1954", doi="10.1021/ie50539a021"),
     "B54: near-duplicate trap -- DOI ...a438 is a one-page item with the same title.", False),
    ("anzelius1926uber", P, "article", dict(
        author="A. Anzelius",
        title="{\\\"U}ber Erw{\\\"a}rmung vermittels durchstr{\\\"o}mender Medien",
        journal="Zeitschrift f{\\\"u}r Angewandte Mathematik und Mechanik", volume="6",
        number="4", pages="291--294", year="1926"),
     "B58: closed, no abstract. The J-function was not read from it. Priority is Anzelius; "
     "the name is Schumann's. The English title in circulation is a translation.", True),
    ("schumann1929heat", P, "article", dict(
        author="T. E. W. Schumann",
        title="Heat transfer: a liquid flowing through a porous prism",
        journal="Journal of the Franklin Institute", volume="208", number="3",
        pages="405--416", year="1929", doi="10.1016/S0016-0032(29)91186-8"),
     "B58: our entry previously carried no title at all.", True),
    ("dodo2000model", P, "article", dict(
        author="D. D. Do and H. D. Do",
        title="A model for water adsorption in activated carbon",
        journal="Carbon", volume="38", number="5", pages="767--773", year="2000",
        doi="10.1016/S0008-6223(99)00159-1"),
     "B56: the word 'new' belongs to the 2009 paper. Only their PRIMARY term carries the "
     "Henry slope. Our primary term is a Langmuir, theirs an n-layer BET -- ours is 'in the "
     "spirit of', not their form. Verified through Buttersack (2019).", True),
    ("dodo2009new", V, "article", dict(
        author="D. D. Do and S. Junpirom and H. D. Do",
        title="A new adsorption--desorption model for water adsorption in activated carbon",
        journal="Carbon", volume="47", number="6", pages="1466--1473", year="2009",
        doi="10.1016/j.carbon.2009.01.039"),
     "Our cluster exponent is a free (sampled) parameter, which is the 2009 model's "
     "treatment, not the 2000 one's. Do not drop Junpirom.", False),
    ("buttersack2019modeling", V, "article", dict(
        author="Christoph Buttersack",
        title="Modeling of type {IV} and {V} sigmoidal adsorption isotherms",
        journal="Physical Chemistry Chemical Physics", volume="21", number="10",
        pages="5614--5626", year="2019", doi="10.1039/C8CP07751G"),
     "Carries the load for the Do--Do Henry-slope verification. He is MILDLY ADVERSARIAL to "
     "the model -- do not imply he endorses it. He calls the family type IV.", False),
    ("wakao1978effect", V, "article", dict(
        author="N. Wakao and T. Funazkri",
        title="Effect of fluid dispersion coefficients on particle-to-fluid mass transfer "
              "coefficients in packed beds",
        journal="Chemical Engineering Science", volume="33", number="10", pages="1375--1384",
        year="1978", doi="10.1016/0009-2509(78)85120-3"),
     "B53: the true source of the 0.7/0.5 coefficients, for NONPOROUS particles, and a lower "
     "bound. Not Ruthven.", False),
    ("edwards1968gas", V, "article", dict(
        author="M. F. Edwards and J. F. Richardson", title="Gas dispersion in packed beds",
        journal="Chemical Engineering Science", volume="23", number="2", pages="109--123",
        year="1968", doi="10.1016/0009-2509(68)87056-3"),
     "Reduces to the 0.5 coefficient only at high particle Peclet number.", False),
    ("levan2019adsorption", V, "incollection", dict(
        author="LeVan and Carta",
        title="Adsorption and ion exchange",
        booktitle="Perry's Chemical Engineers' Handbook", edition="9", publisher="McGraw-Hill",
        year="2019", chapter="16"),
     "Byline changes by edition -- the 7th has a third contributor (Yon). The 9th is the "
     "only one whose authorship was verified from a publisher document.", False),
    ("knox2016limitations", V, "article", dict(
        author="James C. Knox and Armin D. Ebner and M. Douglas LeVan and Robert F. Coker "
               "and James A. Ritter",
        title="Limitations of breakthrough curve analysis in fixed-bed adsorption",
        journal="Industrial \\& Engineering Chemistry Research", volume="55", number="16",
        pages="4734--4748", year="2016", doi="10.1021/acs.iecr.6b00516"),
     "The constant-pattern objection to pre-empt in section 7.", False),

    # ---------------------------------------------------------------- MOF-303
    ("hanikel2021evolution", V, "article", dict(
        author="Nikita Hanikel and Xiaokun Pei and Saumil Chheda and Hao Lyu and WooSeok Jeong "
               "and Joachim Sauer and Laura Gagliardi and Omar M. Yaghi",
        title="Evolution of water structures in metal--organic frameworks for improved "
              "atmospheric water harvesting",
        journal="Science", volume="374", number="6566", pages="454--459", year="2021",
        doi="10.1126/science.abj0890"),
     "B51: 0.45 g/g is Fig. 1A; the ~53 kJ/mol is text S10 / Fig. 4, is the DIFFERENTIAL "
     "adsorption enthalpy, and is negative. 25.0 mol/kg is OUR conversion.", False),
    ("fathieh2018practical", V, "article", dict(
        author="Farhad Fathieh and Markus J. Kalmutzki and Eugene A. Kapustin and "
               "Peter J. Waller and Jingjing Yang and Omar M. Yaghi",
        title="Practical water production from desert air",
        journal="Science Advances", volume="4", number="6", pages="eaat3198", year="2018",
        doi="10.1126/sciadv.aat3198"),
     "The desert device used MOF-801, not MOF-303. Gives MOF-303 0.48 g/g against Hanikel's "
     "0.45 -- reconcile or state which is which.", False),
    ("lassitter2024mass", V, "article", dict(
        author="Thomas Lassitter and Nikita Hanikel and Dennis J. Coyle and others",
        title="Mass transfer in atmospheric water harvesting systems",
        journal="Chemical Engineering Science", volume="285", pages="119430", year="2024",
        doi="10.1016/j.ces.2023.119430"),
     "Do not confuse with Hastings et al. 2024, on which Lassitter is second author.", False),
    ("hastings2024high", V, "article", dict(
        author="Jon Hastings and Thomas Lassitter and Zhiling Zheng and Saumil Chheda and "
               "J. Ilja Siepmann and Laura Gagliardi and Omar M. Yaghi and T. Grant Glover",
        title="High-temperature water adsorption isotherms and ambient temperature water "
              "diffusion rates on water harvesting metal--organic frameworks",
        journal="The Journal of Physical Chemistry C", volume="128", number="27",
        pages="11328--11339", year="2024", doi="10.1021/acs.jpcc.4c01733"),
     "Its 54 kJ/mol is MOF-LA2-1, a DIFFERENT material. It shows the MOF-303 step shifts "
     "with temperature.", False),
    ("bozbiyik2017stepped", V, "article", dict(
        author="Belgin Bozbiyik and Tom Van Assche and Jeroen Lannoeye and Dirk E. De Vos and "
               "Gino V. Baron and Joeri F. M. Denayer",
        title="Stepped water isotherm and breakthrough curves on aluminium fumarate "
              "metal--organic framework: experimental and modelling study",
        journal="Adsorption", volume="23", number="1", pages="185--192", year="2017",
        doi="10.1007/s10450-016-9847-0"),
     "B52: Van Assche was MISSING from our list and the venue was guessed wrong. The stepped "
     "profile is FEED-CONDITION DEPENDENT, not a property of the material.", False),
    ("lee2026scaleup", V, "misc", dict(
        author="Seung-Chan Lee and Chang-Gu Lee and Song-Bae Kim",
        title="Scale-up prediction of breakthrough curves via shape--timescale decomposition "
              "in a hybrid deep learning framework",
        howpublished="SSRN preprint", year="2026", doi="10.2139/ssrn.6874257"),
     "Closest prior art on the warp in our own domain: ONE scalar dilation, single-sigmoid "
     "BTCs. Cite prominently and generously.", False),
]


def bibtex(key, kind, fields):
    lines = [f"@{kind}{{{key},"]
    for k, v in fields.items():
        lines.append(f"  {k} = {{{v}}},")
    lines.append("}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()

    emitted, refused = [], []
    for key, state, kind, fields, note, allow in REFS:
        if key in NOT_EMITTED:
            continue
        if state == V or (state == P and allow):
            emitted.append((key, state, kind, fields, note, allow))
        else:
            refused.append((key, state, note))

    cited = set()
    if os.path.exists(TEX):
        cited = set(re.findall(r"\\cite[tp]?\{([^}]*)\}", open(TEX, encoding="utf-8").read()))
        cited = {k.strip() for group in cited for k in group.split(",")}
    known = {r[0] for r in REFS}
    uncited_in_bib = sorted(cited - {e[0] for e in emitted})
    wrongly_withheld = sorted(cited & set(NOT_EMITTED))
    if wrongly_withheld:
        print("REFUSED -- cited but listed in NOT_EMITTED: " + ", ".join(wrongly_withheld))
        sys.exit(1)

    # B62, twice: a spelled-out given name is an assertion about a real person, so it
    # must occur in a record of what was FETCHED. Initials and surnames pass; a full
    # given name absent from every provenance file refuses the build.
    prov = ""
    for rel in PROVENANCE:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            prov += open(p, encoding="utf-8").read()
    import unicodedata
    prov = "".join(c for c in unicodedata.normalize("NFKD", prov) if not unicodedata.combining(c))
    if not prov:
        sys.exit("no provenance record found -- the given-name gate cannot run, refusing")
    unprovenanced = []
    for key, _, _, fields, _, _ in emitted:
        for name in re.split(r"\s+and\s+", fields.get("author", "")):
            toks = re.sub(r"[{}\\\"'`^~]", "", name).split()
            for tok in toks[:-1]:
                if len(tok) > 1 and not tok.endswith(".") and tok[0].isupper() \
                        and not re.search(rf"\b({re.escape(tok)}|{re.escape(tok.upper())})\b", prov):
                    unprovenanced.append(f"{key}: {tok}")
    if unprovenanced:
        print("REFUSED -- given names with no fetched provenance (rule 11, B62):")
        for u in unprovenanced:
            print(f"  {u}")
        sys.exit(1)
    uncited_emitted = sorted({e[0] for e in emitted} - cited)

    partial = [e for e in emitted if e[1] == P]
    no_via = [e[0] for e in partial if e[0] not in VIA]
    if no_via:
        print("REFUSED -- PARTIAL entries emitted with no VIA (what they were read through): "
              + ", ".join(no_via))
        sys.exit(1)
    with open(os.path.join(ROOT, "paper", "secondary_sources.tex"), "w", encoding="utf-8") as fh:
        fh.write("% GENERATED BY paper/references.py from VIA -- DO NOT EDIT.\n"
                 "\\begin{itemize}\n")
        for e in partial:
            fh.write(f"\\item \\cite{{{e[0]}}}: {VIA[e[0]]}.\n")
        fh.write("\\end{itemize}\n")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("% GENERATED BY paper/references.py -- DO NOT EDIT.\n"
                 "% Only VERIFIED entries, and PARTIAL entries explicitly marked citable\n"
                 "% through a named secondary source, are written here. Rule 8: nothing is\n"
                 "% cited until it has been FETCHED, not searched.\n\n")
        for key, state, kind, fields, note, allow in emitted:
            fh.write(f"% [{state}{' -- cited through a verified secondary source' if allow else ''}]\n")
            if note:
                for ln in re.findall(r".{1,74}(?:\s|$)", note):
                    if ln.strip():
                        fh.write(f"%   {ln.strip()}\n")
            fh.write(bibtex(key, kind, fields) + "\n\n")

    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(emitted)} entries "
          f"({sum(1 for e in emitted if e[1] == V)} VERIFIED, "
          f"{sum(1 for e in emitted if e[1] == P)} PARTIAL cited through a secondary source)")
    for key, state, note in refused:
        print(f"  REFUSED  {key} [{state}] -- {note.splitlines()[0][:90] if note else ''}")
    if uncited_emitted:
        print(f"  NOTE  {len(uncited_emitted)} emitted entr(y/ies) cited by no citation "
              f"(elsarticle-num drops them silently): {', '.join(uncited_emitted)}")
    if uncited_in_bib:
        print(f"\n  {len(uncited_in_bib)} key(s) cited in the manuscript are NOT in the "
              f"bibliography: {', '.join(uncited_in_bib)}")
        sys.exit(1)
    if args.audit:
        print("\naudit — every entry, its state and the trap it exists to avoid:")
        for key, state, _, _, note, allow in REFS:
            flag = "P*" if (state == P and allow) else state[0]
            print(f"  [{flag}] {key:<32} {note.splitlines()[0][:88] if note else ''}")


if __name__ == "__main__":
    main()
