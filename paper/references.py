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
        r"and Cruz, Magalh\~aes and Mendes~\cite{cruz2006generalized}, who attribute the plain factor to the companion "
        r"paper~\cite{glueckauf1947theory}, which is why both are cited",
    "klinkenberg1948numerical":
        r"the breakthrough approximation, read through Seader, Henley and Roper's "
        r"\emph{Separation Process Principles}~\cite{seader2011separation}, which attributes it to the later "
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
        journal="arXiv preprint", year="2026", eprint="2602.21910", archiveprefix="arXiv",
        doi="10.48550/arXiv.2602.21910"),
     "Partial priority on L5's mechanism. Cite prominently and differentiate on the four "
     "axes in CITATIONS.md.", False),
    ("bartolucci2023reno", V, "inproceedings", dict(
        author="Francesca Bartolucci and Emmanuel de B{\\'e}zenac and Bogdan Raoni{\\'c} and "
               "Roberto Molinaro and Siddhartha Mishra and Rima Alaifari",
        title="Representation equivalent neural operators: a framework for alias-free operator learning",
        booktitle="Advances in Neural Information Processing Systems 36 (NeurIPS 2023)",
        pages="69661--69672", year="2023", doi="10.52202/075280-3051"),
     "Six-author list checked character by character against arXiv, DBLP and the NeurIPS "
     "proceedings page. Diagnostic framework -- do NOT cite as a solved problem.", False),
    ("herde2024poseidon", V, "inproceedings", dict(
        author="Maximilian Herde and Bogdan Raoni{\\'c} and Tobias Rohner and Roger K{\\\"a}ppeli "
               "and Roberto Molinaro and Emmanuel de B{\\'e}zenac and Siddhartha Mishra",
        title="Poseidon: efficient foundation models for {PDEs}",
        booktitle="Advances in Neural Information Processing Systems 37 (NeurIPS 2024)",
        pages="72525--72624", year="2024", doi="10.52202/079017-2311"),
     "B42: A23 originally carried MPP's identifier here. Poseidon is 2405.19101. Published "
     "version (NeurIPS 2024) taken from its Crossref record 2026-10-11; seven authors match.", False),
    ("mccabe2023multiple", V, "inproceedings", dict(
        author="Michael McCabe and Bruno {R{\\'e}galdo-Saint Blancard} and Liam Holden Parker and Ruben Ohana "
               "and Miles Cranmer and Alberto Bietti and Michael Eickenberg and Siavash Golkar and "
               "Geraud Krawezik and Francois Lanusse and Mariel Pettee and Tiberiu Tesileanu and "
               "Kyunghyun Cho and Shirley Ho",
        title="Multiple physics pretraining for spatiotemporal surrogate models",
        booktitle="Advances in Neural Information Processing Systems 37 (NeurIPS 2024)",
        pages="119301--119335", year="2024", doi="10.52202/079017-3791"),
     "The identifier A23 had attached to Poseidon. Published at NeurIPS 2024 under a changed title "
     "(arXiv 2310.02994 was 'Multiple physics pretraining for physical surrogate models'); record and "
     "fourteen authors from Crossref 2026-10-11.", False),
    ("krass2025mofsimbench", V, "article", dict(
        author="Hendrik Kra{\\ss} and Ju Huang and Seyed Mohamad Moosavi",
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
        title="Rapid cycling and exceptional yield in a metal--organic framework water harvester",
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
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04. The desert device used MOF-801, not MOF-303; gives MOF-303 0.48 g/g against Hanikel's 0.45 -- state which is which. (Merged from a duplicate entry, 2026-10-11.)", False),
    ("furukawa2014water", V, "article", dict(
        author="Hiroyasu Furukawa and Felipe G{\\'a}ndara and Yue-Biao Zhang and Juncong Jiang and Wendy L. Queen and Matthew R. Hudson and Omar M. Yaghi",
        title="Water adsorption in porous metal--organic frameworks and related materials",
        journal="Journal of the American Chemical Society",
        volume="136",
        number="11",
        pages="4369--4381",
        year="2014",
        doi="10.1021/ja500330a"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("solovyeva2021cau", V, "article", dict(
        author="Marina V. Solovyeva and Alexandr I. Shkatulov and Larisa G. Gordeeva and Elizaveta A. Fedorova and Tamara A. Krieger and Yuri I. Aristov",
        title="Water vapor adsorption on {CAU-10-\\textit{X}}: effect of functional groups on adsorption equilibrium and mechanisms",
        journal="Langmuir",
        volume="37",
        number="2",
        pages="693--702",
        year="2021",
        doi="10.1021/acs.langmuir.0c02729"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("frohlich2016water", V, "article", dict(
        author="Dominik Fr{\\\"o}hlich and Evangelia Pantatosaki and Panagiotis D. Kolokathis and Karen Markey and Helge Reinsch and Max Baumgartner and Monique A. van der Veen and Dirk E. {De Vos} and Norbert Stock and George K. Papadopoulos and Stefan K. Henninger and Christoph Janiak",
        title="Water adsorption behaviour of {CAU-10-H}: a thorough investigation of its structure--property relationships",
        journal="Journal of Materials Chemistry A",
        volume="4",
        number="30",
        pages="11859--11869",
        year="2016",
        doi="10.1039/c6ta01757f"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("laurenz2020novel", V, "article", dict(
        author="Eric Laurenz and Gerrit F{\\\"u}ldner and Lena Schnabel and Gerhard Schmitz",
        title="A novel approach for the determination of sorption equilibria and sorption enthalpy used for {MOF} aluminium fumarate with water",
        journal="Energies",
        volume="13",
        number="11",
        pages="3003",
        year="2020",
        doi="10.3390/en13113003"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("solovyeva2021mil", V, "article", dict(
        author="Marina Solovyeva and Irina Krivosheeva and Larisa Gordeeva and Yuri Aristov",
        title="{MIL-160} as an adsorbent for atmospheric water harvesting",
        journal="Energies",
        volume="14",
        number="12",
        pages="3586",
        year="2021",
        doi="10.3390/en14123586"),
     "Water-MOF placement (referee M10, results/water_mofs.json); value, location and quote in research/water_mof_parameters.json. Crossref record 2026-10-04.", False),
    ("aumond2026adsorption", V, "article", dict(
        author="Thibaud Aumond and Micka{\\\"e}le Bonneau and C{\\'e}cile Daniel and Miriam Perbet and Francis Meunier and David Farrusseng",
        title="Adsorption performances of water-stable {MIL-160(Al)} at scale: an alternative to {FAM-Z02} in water harvesting and chillers",
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
        title="Record atmospheric fresh water capture and heat transfer with a material operating at the water uptake reversibility limit",
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
        journal="arXiv preprint", year="2026", eprint="2601.09491", archiveprefix="arXiv",
        doi="10.48550/arXiv.2601.09491"),
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
        author="Pratik Rathore and Weimu Lei and Zachary Frangella and Lu Lu and Madeleine Udell",
        title="Challenges in training {PINNs}: a loss landscape perspective",
        booktitle="Proceedings of the 41st International Conference on Machine Learning",
        series="Proceedings of Machine Learning Research", volume="235",
        pages="42159--42191", year="2024", eprint="2402.01868", archiveprefix="arXiv"),
     "The Adam-then-L-BFGS polish (Q4). Full names and pages from the PMLR v235 page and the "
     "arXiv record (2026-10-11); PMLR issues no DOI.", False),
    ("lu2021learning", V, "article", dict(
        author="Lu Lu and Pengzhan Jin and Guofei Pang and Zhongqiang Zhang and "
               "George Em Karniadakis",
        title="Learning nonlinear operators via {DeepONet} based on the universal "
              "approximation theorem of operators",
        journal="Nature Machine Intelligence", volume="3", number="3", pages="218--229",
        year="2021", doi="10.1038/s42256-021-00302-5"),
     "The original DeepONet. Crossref record read 2026-10-12.", False),
    ("li2021fourier", V, "inproceedings", dict(
        author="Zongyi Li and Nikola Kovachki and Kamyar Azizzadenesheli and Burigede Liu and "
               "Kaushik Bhattacharya and Andrew Stuart and Anima Anandkumar",
        title="Fourier neural operator for parametric partial differential equations",
        booktitle="International Conference on Learning Representations (ICLR 2021)",
        year="2021", eprint="2010.08895", archiveprefix="arXiv"),
     "The original FNO. Authors from the arXiv record, venue from the ICLR 2021 poster page "
     "(iclr.cc, 2026-10-12); ICLR 2021 has no paginated proceedings and no DOI.", False),
    ("liu2025kan", V, "inproceedings", dict(
        author="Ziming Liu and Yixuan Wang and Sachin Vaidya and Fabian Ruehle and "
               "James Halverson and Marin Solja{\\v{c}}i{\\'c} and Thomas Y. Hou and Max Tegmark",
        title="{KAN}: {Kolmogorov--Arnold} networks",
        booktitle="International Conference on Learning Representations (ICLR 2025)",
        pages="70367--70413", year="2025", eprint="2404.19756", archiveprefix="arXiv"),
     "The original KAN. Authors from the arXiv record; venue and pages from the "
     "proceedings.iclr.cc citation metadata (2026-10-12); no DOI.", False),

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
        author="Julia M. Rohrer and Warren Tierney and Eric L. Uhlmann and Lisa M. DeBruine and "
               "Tom Heyman and Benedict Jones and Stefan C. Schmukle and Raphael Silberzahn and "
               "Rebecca M. Will{\\'e}n and Rickard Carlsson and Richard E. Lucas and Julia Strand and "
               "Simine Vazire and Jessica K. Witt and Thomas R. Zentall and Christopher F. Chabris "
               "and Tal Yarkoni",
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
        journal="arXiv preprint", year="2024", eprint="2407.17539", archiveprefix="arXiv",
        doi="10.48550/arXiv.2407.17539"),
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
    ("gowrachari2025cross", V, "incollection", dict(
        author="Harshith Gowrachari and Giovanni Stabile and Gianluigi Rozza",
        title="Model reduction for transport-dominated problems via cross-correlation based "
              "snapshot registration",
        booktitle="Scientific Machine Learning", series="SEMA SIMAI Springer Series",
        publisher="Springer Nature Switzerland", pages="199--218", year="2026",
        doi="10.1007/978-3-032-11527-0_10"),
     "A NEGATIVE result in our favour: registration ROM has not been taken into "
     "separation-process column fields. A search summary claimed otherwise and was wrong.",
     False),
    ("ohlberger2016reduced", V, "inproceedings", dict(
        author="Mario Ohlberger and Stephan Rave",
        title="Reduced basis methods: success, limitations and future challenges",
        booktitle="Proceedings of the Conference Algoritmy 2016", pages="1--12", year="2016",
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
        journal="The Annals of Statistics", volume="20", number="3", pages="1266--1305", year="1992",
        doi="10.1214/aos/1176348769"),
     "B38: the correct LANDMARK-registration ancestor. Pages read from the Crossref record "
     "2026-10-25 (rsc.bst requires them).", False),
    ("ramsay1998curve", V, "article", dict(
        author="J. O. Ramsay and Xiaochun Li", title="Curve registration",
        journal="Journal of the Royal Statistical Society: Series B (Statistical Methodology)", volume="60",
        number="2", pages="351--363", year="1998", doi="10.1111/1467-9868.00129"),
     "DOI trap: ...00115 is a DIFFERENT JRSS-B 1998 paper. The landmark-FREE branch, cited "
     "as the canonical curve-registration reference and as the contrast.", False),

    # ------------------------------------------------------- adsorption and transport
    ("vangenuchten1982analytical", V, "techreport", dict(
        author="M. Th. van Genuchten and W. J. Alves",
        title="Analytical solutions of the one-dimensional convective-dispersive solute "
              "transport equation",
        institution="U.S. Department of Agriculture, Agricultural Research Service",
        type="Technical Bulletin", number="1661", year="1982"),
     "B10/B59: defines the third- or FLUX-type inlet [9b] and cites Ogata & Banks for the "
     "first-type. It never uses the name 'Danckwerts'. It also states that the flux-type "
     "condition conserves mass where the concentration-type does not -- which is B8.", False),
    ("ogata1961solution", V, "techreport", dict(
        author="Akio Ogata and R. B. Banks",
        title="A solution of the differential equation of longitudinal dispersion in porous media",
        institution="U.S. Geological Survey", type="Professional Paper", number="411-A",
        pages="A1--A7", year="1961", doi="10.3133/pp411A"),
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
        title="Theory of chromatography. {Part} {IV}. {The} influence of incomplete equilibrium "
              "on the front boundary of chromatograms and on the effectiveness of separation",
        journal="Journal of the Chemical Society (Resumed)", pages="1315", year="1947",   # no volume in 1947
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
        title="{{\\\"U}ber Erw{\\\"a}rmung vermittels durchstr{\\\"o}mender Medien}",
        journal="Zeitschrift f{\\\"u}r Angewandte Mathematik und Mechanik", volume="6",
        number="4", pages="291--294", year="1926", doi="10.1002/zamm.19260060404"),
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
        author="M. Douglas LeVan and Giorgio Carta and James A. Ritter and Krista S. Walton",
        title="Adsorption and ion exchange",
        editor="Don W. Green and Marylee Z. Southard",
        booktitle="Perry's Chemical Engineers' Handbook", edition="9",
        publisher="McGraw-Hill Education", year="2019", type="{S}ection", chapter="16",
        isbn="9780071834087"),
     "Byline changes by edition -- the 7th has a third contributor (Yon). The 9th's four "
     "authors (LeVan, Carta, Ritter, Walton) are from the publisher's citation metadata on "
     "AccessEngineering, read 2026-10-11; our entry previously listed two, as surnames.", False),
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
    ("lassitter2024mass", V, "article", dict(
        author="Thomas Lassitter and Nikita Hanikel and Dennis J. Coyle and Mohammad I. Hossain and "
               "Bryce Lipinski and Michael O'Brien and David B. Hall and Jon Hastings and "
               "Juan Borja and Travis O'Neil and S. Ephraim Neumann and David R. Moore and "
               "Omar M. Yaghi and T. Grant Glover",
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
        author="Belgin Bozbiyik and Tom {Van Assche} and Jeroen Lannoeye and Dirk E. {De Vos} and "
               "Gino V. Baron and Joeri F. M. Denayer",
        title="Stepped water isotherm and breakthrough curves on aluminium fumarate "
              "metal--organic framework: experimental and modelling study",
        journal="Adsorption", volume="23", number="1", pages="185--192", year="2017",
        doi="10.1007/s10450-016-9847-0"),
     "B52: Van Assche was MISSING from our list and the venue was guessed wrong. The stepped "
     "profile is FEED-CONDITION DEPENDENT, not a property of the material.", False),
    ("lee2026scaleup", V, "article", dict(
        author="Seung-Chan Lee and Chang-Gu Lee and Song-Bae Kim",
        title="Scale-up prediction of breakthrough curves via shape--timescale decomposition "
              "in a hybrid deep learning framework",
        journal="Chemical Engineering Journal", volume="549", pages="183235", year="2026",
        doi="10.1016/j.cej.2026.183235"),
     "Closest prior art on the warp in our own domain: ONE scalar dilation, single-sigmoid "
     "BTCs. Published version (Crossref 2026-10-25); the SSRN preprint 10.2139/ssrn.6874257 "
     "was cited before.", False),

    # ------------------------------------- Digital Discovery revision (Crossref 2026-10-25)
    ("abaei2026benchmark", V, "article", dict(
        author="Shayan Abaei and Hosein Alimardani and Mohammad Fakhroleslam and Fatemeh Eslami "
               "and Mehrdad Asgari",
        title="Benchmark maturity in {MOF} adsorption machine learning: when do conclusions become "
              "scientifically reliable?",
        journal="Digital Discovery", volume="5", number="10", pages="4541--4553", year="2026",
        doi="10.1039/d6dd00351f"),
     "Nearest Digital Discovery neighbour: MOF benchmark rankings stabilise only at large N.", False),
    ("burark2024codbench", V, "article", dict(
        author="Priyanshu Burark and Karn Tiwari and Meer Mehran Rashid and {Prathosh A. P.} and "
               "N. M. Anoop Krishnan",
        title="{CoDBench}: a critical evaluation of data-driven models for continuous dynamical systems",
        journal="Digital Discovery", volume="3", number="6", pages="1172--1181", year="2024",
        doi="10.1039/d4dd00028e"),
     "The journal's operator-learning benchmark.", False),
    ("witman2025matfold", V, "article", dict(
        author="Matthew D. Witman and Peter Schindler",
        title="{MatFold}: systematic insights into materials discovery models' performance through "
              "standardized cross-validation protocols",
        journal="Digital Discovery", volume="4", number="3", pages="625--635", year="2025",
        doi="10.1039/d4dd00250d"),
     "Out-of-distribution splits for materials models; our held-out split is in-distribution.", False),
    ("choe2026extrapolation", V, "article", dict(
        author="Jonghwi Choe and Shuan Chen and Yousung Jung",
        title="Assessing the extrapolation capability of template-free retrosynthesis models",
        journal="Digital Discovery", volume="5", number="6", pages="2591--2599", year="2026",
        doi="10.1039/d6dd00072j"),
     "A quantified negative generalisation result in Digital Discovery.", False),
    ("zhu2026deep", V, "article", dict(
        author="Junxiao Zhu and Shiyi Wang and Ziming Liang and Liang Qin and Chengxiao Wang and "
               "Deyun Ma and Lin Chen",
        title="Benchmarking machine learning for therapeutic deep eutectic solvent screening: dataset "
              "construction, cross-source generalization failure, and applicability-boundary analysis",
        journal="Digital Discovery", year="2026", doi="10.1039/d6dd00521g"),
     "Advance article (no volume or pages in Crossref on 2026-10-25).", False),
    ("dehoop2022cost", V, "article", dict(
        author="Maarten V. de Hoop and Daniel Zhengyu Huang and Elizabeth Qian and Andrew M. Stuart",
        title="The cost-accuracy trade-off in operator learning with neural networks",
        journal="Journal of Machine Learning", volume="1", number="3", pages="299--341", year="2022",
        doi="10.4208/jml.220509"),
     "Cost against accuracy for POD-NN, DeepONet, PCA-Net and FNO: our cost section is the "
     "adsorption-bed instance.", False),
    ("huang2026cost", V, "misc", dict(
        author="Daniel Zhengyu Huang and Andrew M. Stuart",
        title="Cost-accuracy trade-offs: neural operator vs classical numerical solver",
        howpublished="arXiv preprint", year="2026", eprint="2609.24021", archiveprefix="arXiv"),
     "Classical solvers against neural operators at matched cost (arXiv record 2026-10-25).", False),
    ("bhattacharya2021model", V, "article", dict(
        author="Kaushik Bhattacharya and Bamdad Hosseini and Nikola B. Kovachki and Andrew M. Stuart",
        title="Model reduction and neural networks for parametric {PDEs}",
        journal="The SMAI Journal of Computational Mathematics", volume="7", pages="121--157",
        year="2021", doi="10.5802/smai-jcm.74"),
     "PCA-Net: the projection-plus-regression error split our eq. (split) applies.", False),
    ("wang2025rbdeeponet", V, "misc", dict(
        author="Yueqi Wang and Guang Lin",
        title="Reduced-basis deep operator learning for parametric {PDEs} with independently varying "
              "boundary and source data",
        howpublished="arXiv preprint", year="2025", eprint="2511.18260", archiveprefix="arXiv"),
     "Separates reduced-basis approximation error from learning error (arXiv record 2026-10-25).", False),
    ("galanti2025towards", V, "article", dict(
        author="Mattia Galanti and Mik Janssen and Ivo Roghair and Jean-Yves Dieulot and "
               "Pejman Shoeibi Omrani and Jurriaan Boon and Martin van Sint Annaland",
        title="Towards surrogate modeling for adsorption processes using physics-informed neural networks",
        journal="Processes", volume="13", number="9", pages="2824", year="2025",
        doi="10.3390/pr13092824"),
     "Direct precedent for L4: PINN surrogates of adsorption processes.", False),
    ("sircar2000why", V, "article", dict(
        author="S. Sircar and J.R. Hufton",
        title="Why does the linear driving force model for adsorption kinetics work?",
        journal="Adsorption", volume="6", number="2", pages="137--147", year="2000",
        doi="10.1023/A:1008965317983"),
     "LDF validity for nonlinear isotherms: the scope of our kinetic closure.", False),
    ("kim2017water", V, "article", dict(
        author="Hyunho Kim and Sungwoo Yang and Sameer R. Rao and Shankar Narayanan and "
               "Eugene A. Kapustin and Hiroyasu Furukawa and Ari S. Umans and Omar M. Yaghi and "
               "Evelyn N. Wang",
        title="Water harvesting from air with metal-organic frameworks powered by natural sunlight",
        journal="Science", volume="356", number="6336", pages="430--434", year="2017",
        doi="10.1126/science.aam8743"),
     "Device-level context for MOF water harvesting.", False),
    ("kim2018adsorption", V, "article", dict(
        author="Hyunho Kim and Sameer R. Rao and Eugene A. Kapustin and Lin Zhao and Sungwoo Yang "
               "and Omar M. Yaghi and Evelyn N. Wang",
        title="Adsorption-based atmospheric water harvesting device for arid climates",
        journal="Nature Communications", volume="9", number="1", pages="1191", year="2018",
        doi="10.1038/s41467-018-03162-7"),
     "Device-level context: a harvester operated in an arid climate.", False),
    ("lapotin2019adsorption", V, "article", dict(
        author="Alina LaPotin and Hyunho Kim and Sameer R. Rao and Evelyn N. Wang",
        title="Adsorption-based atmospheric water harvesting: impact of material and component "
              "properties on system-level performance",
        journal="Accounts of Chemical Research", volume="52", number="6", pages="1588--1597",
        year="2019", doi="10.1021/acs.accounts.9b00062"),
     "Material-to-device screening framing.", False),
    ("goeminne2025ab", V, "article", dict(
        author="Ruben Goeminne and {Van Speybroeck}, Veronique",
        title="Ab initio predictions of adsorption in flexible metal--organic frameworks for water "
              "harvesting applications",
        journal="Journal of the American Chemical Society", volume="147", number="4",
        pages="3615--3630", year="2025", doi="10.1021/jacs.4c15287"),
     "Structure-to-isotherm models that would feed the parameter-to-coefficient map.", False),
    ("nasiri2026process", V, "article", dict(
        author="{Nasiri Ghiri}, Maryam and Hamid Reza Nasriani and Mohammad Bagheri and Leila Khajenoori "
               "and Samira Khani Rasmussen and Andrei Chamchine",
        title="Process-informed optimal design principles for cooperative step-isotherm adsorbents in "
              "direct air capture using {ANN}-accelerated {TVSA} modelling",
        journal="Chemical Engineering Journal Advances", volume="27", pages="101283", year="2026",
        doi="10.1016/j.ceja.2026.101283"),
     "Closest application overlap: an ANN surrogate of a TVSA bed over step-isotherm sorbent "
     "parameters, for scalar KPIs (SEC, productivity) and optimisation; no held-out-material "
     "error, no field surrogate, no coarse baseline (abstract via OpenAlex 2026-10-25).", False),
    ("nasiri2026surrogate", V, "article", dict(
        author="{Nasiri Ghiri}, Maryam and Hamid Reza Nasriani and Leila Khajenoori and "
               "Samira Khani Rasmussen and Karl Williams",
        title="Surrogate-assisted cyclic performance optimisation of direct air capture using "
              "amine-functionalised metal--organic frameworks",
        journal="Separation and Purification Technology", volume="383", pages="136177", year="2026",
        doi="10.1016/j.seppur.2025.136177"),
     "A recent process surrogate on a MOF sorbent (abstract via OpenAlex).", False),
    ("liske2026extended", V, "article", dict(
        author="Gwyneth Liske and Arvind Rajendran",
        title="Extended batch adsorber analogue model ({e-BAAM}) for rapid evaluation of {CO$_2$} "
              "capture pressure swing adsorption cycles",
        journal="The Canadian Journal of Chemical Engineering", year="2026", doi="10.1002/cjce.70453",
        note="DOI: 10.1002/cjce.70453"),
     "Reduced-physics screening model: cheap physics as the competitor of learned surrogates. "
     "Online 2026, no volume or pages in Crossref on 2026-10-25.", False),
    ("alkhatib2026machine", V, "article", dict(
        author="Nour Alkhatib and Saifeldeen Abed Alrhman and Serdal Kirmizialtin",
        title="Machine learning highlights chemistry as the key factor in metal--organic frameworks "
              "for atmospheric water harvesting",
        journal="Molecular Systems Design \\& Engineering", volume="11", number="1", pages="50--61",
        year="2026", doi="10.1039/d5me00101c"),
     "Materials-level ML for MOF water harvesting (GCMC + ML).", False),
    ("arjmandi2026next", V, "article", dict(
        author="M. Arjmandi and E. Ayta{\\c{c}} and M. Khayet and N. Hilal",
        title="Next-generation {MOFs} for atmospheric water harvesting: the role of machine learning "
              "techniques",
        journal="Coordination Chemistry Reviews", volume="548", pages="217211", year="2026",
        doi="10.1016/j.ccr.2025.217211"),
     "Review of ML for MOF water harvesting; Crossref gives initials only.", False),
    ("han2025machine", V, "article", dict(
        author="Bo Han and Anutosh Chakraborty",
        title="Machine learning optimized adsorption heat transformations from adsorbents screening to "
              "enhanced performances",
        journal="Energy Conversion and Management", volume="344", pages="120272", year="2025",
        doi="10.1016/j.enconman.2025.120272"),
     "No public abstract (Crossref, OpenAlex 2026-10-25): cite only for what the title states.", False),
    ("han2025optimizing", V, "article", dict(
        author="Bo Han and Mai Sheng Ng and Anutosh Chakraborty",
        title="Optimizing metal-organic frameworks for adsorption-based atmospheric water harvesting: a "
              "systematic evaluation of pristine and modified {MOFs} for enhanced performance in diverse "
              "climates",
        journal="Chemical Engineering Journal", volume="521", pages="166607", year="2025",
        doi="10.1016/j.cej.2025.166607"),
     "No public abstract: cite only for what the title states.", False),
    ("wyder2025common", V, "inproceedings", dict(
        author="Philippe Wyder and Judah Goldfeder and Alexey Yermakov and Yue Zhao and Stefano Riva "
               "and Jan Williams and David Zoro and Amy Rude and Matteo Tomasetto and Joe Germany and "
               "Joseph Bakarji and Georg Maierhofer and Miles Cranmer and J. Nathan Kutz",
        title="Common task framework for a critical evaluation of scientific machine learning algorithms",
        booktitle="Advances in Neural Information Processing Systems 38 (Datasets and Benchmarks Track)",
        pages="188884--188901", year="2025", doi="10.52202/085713-5677"),
     "Version of record (NeurIPS 38), Crossref record read 2026-10-27; earlier cited as "
     "arXiv:2510.23166.", False),
    ("vantegelen2026late", V, "misc", dict(
        author="Eva van Tegelen and Taniya Kapoor and George A. K. van Voorn and Peter van Heijster and "
               "Ioannis N. Athanasiadis",
        title="Late fusion neural operators for extrapolation across parameter space in partial "
              "differential equations",
        howpublished="arXiv preprint", year="2026", eprint="2604.16721", archiveprefix="arXiv"),
     "How parameters enter the model governs extrapolation: supports 'the map binds'.", False),
    ("nadeau2003inference", V, "article", dict(
        author="Claude Nadeau and Yoshua Bengio",
        title="Inference for the generalization error",
        journal="Machine Learning", volume="52", number="3", pages="239--281", year="2003",
        doi="10.1023/A:1024068626366"),
     "Cross-validation variance has no unbiased estimator: our intervals are conditional on the "
     "fitted models.", False),

    # ------------------------------------------- the secondary sources named in VIA
    ("cruz2006generalized", V, "article", dict(
        author="P. Cruz and F. D. Magalh{\\~a}es and A. Mendes",
        title="Generalized linear driving force approximation for adsorption of multicomponent mixtures",
        journal="Chemical Engineering Science", volume="61", number="11", pages="3519--3531",
        year="2006", doi="10.1016/j.ces.2006.01.001"),
     "Read for the attribution of the plain LDF factor (their Eq. 44) to Glueckauf and Coates 1947. "
     "Record from Crossref, 2026-10-12. Named in VIA but missing from the list until the final read.", False),
    ("seader2011separation", V, "book", dict(
        author="J. D. Seader and Ernest J. Henley and D. Keith Roper",
        title="Separation Process Principles: Chemical and Biochemical Operations",
        edition="3", publisher="Wiley", year="2011", isbn="9780470481837"),
     "The secondary source for the Klinkenberg erf approximation and its 1954 attribution (B54). "
     "Edition record from Open Library (ISBN 9780470481837), 2026-10-12.", False),

    # ------------------------------------------- asked for by the 2026-10-25 internal referees
    ("lu2022comprehensive", V, "article", dict(
        author="Lu Lu and Xuhui Meng and Shengze Cai and Zhiping Mao and Somdatta Goswami and "
               "Zhongqiang Zhang and George Em Karniadakis",
        title="A comprehensive and fair comparison of two neural operators (with practical extensions) "
              "based on {FAIR} data",
        journal="Computer Methods in Applied Mechanics and Engineering", volume="393", pages="114778",
        year="2022", doi="10.1016/j.cma.2022.114778"),
     "POD-DeepONet (fixed POD trunk, learned branch). Crossref record read 2026-10-25.", False),
    ("lanthaler2022error", V, "article", dict(
        author="Samuel Lanthaler and Siddhartha Mishra and George E. Karniadakis",
        title="Error estimates for {DeepONets}: a deep learning framework in infinite dimensions",
        journal="Transactions of Mathematics and Its Applications", volume="6", number="1",
        pages="tnac001", year="2022", doi="10.1093/imatrm/tnac001"),
     "Encoder/approximator/reconstructor error decomposition of DeepONet. Crossref record read "
     "2026-10-25.", False),
    ("kovachki2023neural", V, "article", dict(
        author="Nikola Kovachki and Zongyi Li and Burigede Liu and Kamyar Azizzadenesheli and "
               "Kaushik Bhattacharya and Andrew Stuart and Anima Anandkumar",
        title="Neural operator: learning maps between function spaces with applications to {PDEs}",
        journal="Journal of Machine Learning Research", volume="24", number="89", pages="1--97",
        year="2023", url="https://jmlr.org/papers/v24/21-1524.html"),
     "No DOI (JMLR). Citation metadata read from the jmlr.org article page 2026-10-25.", False),
    ("kalmutzki2018metal", V, "article", dict(
        author="Markus J. Kalmutzki and Christian S. Diercks and Omar M. Yaghi",
        title="Metal--organic frameworks for water harvesting from air",
        journal="Advanced Materials", volume="30", number="37", pages="1704304", year="2018",
        doi="10.1002/adma.201704304"),
     "Review of MOF water harvesting. Crossref record read 2026-10-25.", False),
    ("delange2015adsorption", V, "article", dict(
        author="Martijn F. de Lange and Karlijn J. F. M. Verouden and Thijs J. H. Vlugt and "
               "Jorge Gascon and Freek Kapteijn",
        title="Adsorption-driven heat pumps: the potential of metal--organic frameworks",
        journal="Chemical Reviews", volume="115", number="22", pages="12205--12250", year="2015",
        doi="10.1021/acs.chemrev.5b00059"),
     "Water-sorption MOFs and step-shaped isotherms for heat pumps. Crossref record read 2026-10-25.",
     False),
    ("farmahini2021performance", V, "article", dict(
        author="Amir H. Farmahini and Shreenath Krishnamurthy and Daniel Friedrich and Stefano Brandani "
               "and Lev Sarkisov",
        title="Performance-based screening of porous materials for carbon capture",
        journal="Chemical Reviews", volume="121", number="17", pages="10666--10741", year="2021",
        doi="10.1021/acs.chemrev.0c01266"),
     "Process-level against material-KPI screening. Crossref record read 2026-10-25.", False),

    # ------------------------------- 2026-10-27 literature check (Crossref / arXiv records read that day)
    ("halder2022non", V, "article", dict(
        author="Rakesh Halder and Krzysztof J. Fidkowski and Kevin J. Maki",
        title="Non-intrusive reduced-order modeling using convolutional autoencoders",
        journal="International Journal for Numerical Methods in Engineering", volume="123", number="21",
        pages="5369--5390", year="2022", doi="10.1002/nme.7072"),
     "In-distribution precedent: POD projection error keeps falling while POD-GPR prediction error "
     "flattens, attributed to the coefficients.", False),
    ("franco2023mesh", V, "article", dict(
        author="Nicola Rares Franco and Andrea Manzoni and Paolo Zunino",
        title="Mesh-informed neural networks for operator learning in finite element spaces",
        journal="Journal of Scientific Computing", volume="97", number="2", pages="35", year="2023",
        doi="10.1007/s10915-023-02331-1"),
     "POD projection error tiny; the branch net is responsible for the error (in distribution).", False),
    ("brivio2024error", V, "article", dict(
        author="Simone Brivio and Stefania Fresca and Nicola Rares Franco and Andrea Manzoni",
        title="Error estimates for {POD-DL-ROMs}: a deep learning framework for reduced order modeling of "
              "nonlinear parametrized {PDEs} enhanced by proper orthogonal decomposition",
        journal="Advances in Computational Mathematics", volume="50", number="3", pages="33", year="2024",
        doi="10.1007/s10444-024-10110-1"),
     "Theory separating POD-dimension error from network and sampling error.", False),
    ("grimm2022machine", V, "article", dict(
        author="Alexa Grimm and Matteo Gazzani",
        title="A machine learning-aided equilibrium model of {VTSA} processes for sorbents screening applied "
              "to {CO2} capture from diluted sources",
        journal="Industrial \\& Engineering Chemistry Research", volume="61", number="37",
        pages="14004--14019", year="2022", doi="10.1021/acs.iecr.2c01695"),
     "Reduced-physics model with an ML correction used for sorbent screening.", False),
    ("bezrukov2023metal", V, "article", dict(
        author="Andrey A. Bezrukov and Daniel J. O'Hearn and Victoria Gasc{\\'o}n-P{\\'e}rez and Shaza Darwish "
               "and Amrit Kumar and Suresh Sanda and Naveen Kumar and Kurt Francis and Michael J. Zaworotko",
        title="Metal--organic frameworks as regeneration optimized sorbents for atmospheric water harvesting",
        journal="Cell Reports Physical Science", volume="4", number="2", pages="101252", year="2023",
        doi="10.1016/j.xcrp.2023.101252"),
     "Isotherm-shape-driven cycling comparison of water-harvesting MOFs.", False),
    ("abdelwadood2026ai", V, "article", dict(
        author="Samar Abdelwadood and Seda Rouxel and Samuel Mao and Ludovic F. Dum{\\'e}e",
        title="{AI}-driven discovery of high-performance metal--organic frameworks for next-gen atmospheric "
              "water harvesting",
        journal="Journal of Materials Chemistry A", volume="14", number="38", pages="25349--25364", year="2026",
        doi="10.1039/d6ta01583b"),
     "Leave-one-MOF-out ML for water uptake, not bed dynamics.", False),
    ("chatain2025numerical", V, "misc", dict(
        author="Patrick Chatain and Michael Rizvi-Martel and Guillaume Rabusseau and Adam Oberman",
        title="Numerical {PDE} solvers outperform neural {PDE} solvers",
        howpublished="arXiv preprint", year="2025", eprint="2507.21269", archiveprefix="arXiv",
        doi="10.48550/arXiv.2507.21269"),
     "A differentiable finite-difference model with learned coefficients beats FNO by one to two "
     "orders of magnitude, in and out of distribution (arXiv abstract read 2026-10-27).", False),
    ("glover2026accelerating", V, "article", dict(
        author="Alex Glover and Maria M. Papathanasiou and Ronny Pini",
        title="Accelerating simulation and optimisation of cyclic adsorption processes with "
              "differentiable programming",
        journal="Computers \\& Chemical Engineering", volume="216", pages="109904", year="2027",
        doi="10.1016/j.compchemeng.2026.109904"),
     "Speeds up the mechanistic adsorption solver itself (about 20x to cyclic steady state). Published "
     "version (January 2027 issue), Crossref record read 2026-10-27; earlier arXiv:2606.21523.", False),
    ("charalambous2024holistic", V, "article", dict(
        author="Charithea Charalambous and Elias Moubarak and Johannes Schilling and "
               "{Sanchez Fernandez}, Eva and Jin-Yu Wang and Laura Herraiz and Fergus Mcilwaine and "
               "Shing Bo Peh and Matthew Garvin and Kevin Maik Jablonka and Seyed Mohamad Moosavi and "
               "{Van Herck}, Joren and {Yurdusen Ozturk}, Aysu and Alireza Pourghaderi and Ah-Young Song "
               "and Georges Mouchaham and Christian Serre and Jeffrey A. Reimer and Andr{\\'e} Bardow and "
               "Berend Smit and Susana Garcia",
        title="A holistic platform for accelerating sorbent-based carbon capture",
        journal="Nature", volume="632", number="8023", pages="89--94", year="2024",
        doi="10.1038/s41586-024-07683-8"),
     "PrISMa: process-informed screening of sorbents, including MOFs, with process design, "
     "techno-economics and life-cycle assessment. Crossref record and abstract read 2026-10-27.", False),
    ("wang2026bridging", V, "article", dict(
        author="Yiqi Wang and Yongchul G. Chung and Weixiong Wu and Wei Li and Song Li",
        title="Bridging the gap between materials and engineering: large-scale screening of "
              "metal--organic frameworks for adsorption cooling from device level",
        journal="Advanced Energy Materials", volume="16", number="5", pages="e04672", year="2026",
        doi="10.1002/aenm.202504672"),
     "MOF screening for adsorption cooling that integrates device-level heat and mass transport. "
     "Crossref record and abstract read 2026-10-27 (online 2025, issue 2026).", False),
    ("harriman2025optimizing", V, "article", dict(
        author="Charles Harriman and Qia Ke and Thijs J. H. Vlugt and Ashlee J. Howarth and Cory M. Simon",
        title="Optimizing mixtures of metal--organic frameworks for robust and bespoke passive "
              "atmospheric water harvesting",
        journal="ACS Engineering Au", volume="5", number="6", pages="707--725", year="2025",
        doi="10.1021/acsengineeringau.5c00051"),
     "Water delivery of MOF adsorbent beds for passive harvesting, from water isotherms and "
     "weather conditions. Crossref record and abstract read 2026-10-27.", False),
    ("li2025probing", V, "article", dict(
        author="Kangming Li and Andre Niyongabo Rubungo and Xiangyun Lei and Daniel Persaud and "
               "Kamal Choudhary and Brian DeCost and Adji Bousso Dieng and Jason Hattrick-Simpers",
        title="Probing out-of-distribution generalization in machine learning for materials",
        journal="Communications Materials", volume="6", pages="9", year="2025",
        doi="10.1038/s43246-024-00731-w"),
     "Many supposedly out-of-distribution materials splits are interpolation. Crossref record read "
     "2026-10-27.", False),
    ("omee2024structure", V, "article", dict(
        author="Sadman Sadeed Omee and Nihang Fu and Rongzhi Dong and Ming Hu and Jianjun Hu",
        title="Structure-based out-of-distribution ({OOD}) materials property prediction: a benchmark study",
        journal="npj Computational Materials", volume="10", pages="144", year="2024",
        doi="10.1038/s41524-024-01316-4"),
     "Materials-specific evidence that random splits overstate performance. Crossref record read "
     "2026-10-27.", False),
    ("michalopoulou2024assessment", V, "article", dict(
        author="Foteini Michalopoulou and Maria M. Papathanasiou",
        title="Assessment of data-driven modeling approaches for chromatographic separation processes",
        journal="AIChE Journal", volume="70", number="12", pages="e18600", year="2024",
        doi="10.1002/aic.18600"),
     "Neural surrogates of a chromatographic column judged on accuracy, interpolation and "
     "simulation time against the high-fidelity model. Crossref record and abstract read 2026-10-27.",
     False),
    ("zhang2024blending", V, "article", dict(
        author="Enrui Zhang and Adar Kahana and Alena Kopani{\\v{c}}{\\'a}kov{\\'a} and Eli Turkel and "
               "Rishikesh Ranade and Jay Pathak and George Em Karniadakis",
        title="Blending neural operators and relaxation methods in {PDE} numerical solvers",
        journal="Nature Machine Intelligence", volume="6", number="11", pages="1303--1313", year="2024",
        doi="10.1038/s42256-024-00910-x"),
     "A neural operator inside an iterative solver, accelerating it rather than replacing it. "
     "Crossref record read 2026-10-27.", False),
    ("kovachki2024operator", V, "incollection", dict(
        author="Nikola B. Kovachki and Samuel Lanthaler and Andrew M. Stuart",
        title="Operator learning: algorithms and analysis",
        booktitle="Numerical Analysis Meets Machine Learning, Handbook of Numerical Analysis", publisher="Elsevier", pages="419--467", year="2024",
        doi="10.1016/bs.hna.2024.05.009"),
     "Standard review of operator learning, including the encoder--decoder error split. Crossref "
     "record read 2026-10-27 (title 'Operator learning', pages 419-467, no author list in Crossref); "
     "authors and full title from arXiv:2402.15715.", False),
    ("koehler2025neural", V, "inproceedings", dict(
        author="Felix Koehler and Nils Thuerey",
        title="Neural emulator superiority: when machine learning for {PDEs} surpasses its training data",
        booktitle="Advances in Neural Information Processing Systems 38", pages="183610--183652",
        year="2025", doi="10.52202/085713-5521"),
     "Counterpoint: an emulator trained on low-fidelity data can beat that solver.", False),
    ("kapoor2023leakage", V, "article", dict(
        author="Sayash Kapoor and Arvind Narayanan",
        title="Leakage and the reproducibility crisis in machine-learning-based science",
        journal="Patterns", volume="4", number="9", pages="100804", year="2023",
        doi="10.1016/j.patter.2023.100804"),
     "Leakage taxonomy; supports splitting and resampling by material.", False),

    # ------------------------------------------------- the data reference (guide, Option C)
    ("batayhi2026code", V, "misc", dict(
        author="Abdulhamid Batayhi",
        title="{Code, results and pre-registrations for: Machine-learning surrogates of MOF water-adsorption beds: the coefficient map, not the basis, limits accuracy on unseen materials}",
        howpublished="Zenodo", note="Version v2.0.1", year="2026",
        doi="10.5281/zenodo.23704400"),
     "The archived release of this repository used for the Digital Discovery submission: v2.0.1, "
     "record read from the Zenodo API 2026-10-27 (title, creator, version, DOI; v2.0.0 is "
     "10.5281/zenodo.23699712). Earlier releases (read 2026-10-12: v1.0.5 is 10.5281/zenodo.23323685; v1.0.4 is 10.5281/zenodo.23312204, v1.0.3 is 10.5281/zenodo.23311637, v1.0.2 is 10.5281/zenodo.23306131, v1.0.1-cmame is 10.5281/zenodo.23305298); first version 10.5281/zenodo.23302587; concept DOI "
     "10.5281/zenodo.23302586 resolves to the latest version. The [dataset] tag is the "
     "guide's marker for production and is removed in the published article.", False),
    ("batayhi2026codeconcept", V, "misc", dict(
        author="Abdulhamid Batayhi",
        title="{Code, results and pre-registrations for: Machine-learning surrogates of MOF water-adsorption "
              "beds: the coefficient map, not the basis, limits accuracy on unseen materials} (all versions)",
        howpublished="Zenodo", note="Concept record; resolves to the most recent version", year="2026",
        doi="10.5281/zenodo.23302586"),
     "Concept DOI of the Zenodo record (DataCite; listed in the v1.0.5 record read 2026-10-12). The "
     "Digital Discovery guidelines ask for the DOIs of both the most recent and the archived version. "
     "Title to be re-read from the record after the release that accompanies this version.", False),
    ("batayhi2026data", V, "misc", dict(
        author="Abdulhamid Batayhi and H. Cankurt",
        title="{Dataset for: Machine-learning surrogates of MOF water-adsorption beds: the "
              "coefficient map, not the basis, limits accuracy on unseen materials}",
        howpublished="Zenodo", year="2026", doi="10.5281/zenodo.23683358"),
     "Our own dataset record. DOI reserved in the Zenodo draft on 2026-10-27 (read from the "
     "upload form); it resolves once the record is published, which must happen before submission. "
     "Title and creators as entered in that form.", False),
]


def bibtex(key, kind, fields):
    # rsc.bst ignores eprint and drops article titles, so an arXiv preprint printed as
    # "arXiv preprint, 2026." with nothing a reader could look up. Every arXiv entry is
    # written as a titled record that names its identifier.
    venue = fields.get("journal") or fields.get("howpublished") or ""
    if fields.get("archiveprefix") == "arXiv" and fields.get("eprint") and venue.startswith("arXiv") \
            and "booktitle" not in fields:          # a published paper keeps its venue
        kind = "misc"
        fields = {k: v for k, v in fields.items() if k != "journal"}
        fields["howpublished"] = f"arXiv preprint, arXiv:{fields['eprint']}"
    # rsc.bst prints no DOI, which for a data or code record is the only way to find it
    # (the journal's data reviewer needs both code DOIs and the dataset DOI in the list)
    # an early-view article (no volume, no pages yet) is found by its DOI, as RSC prints it:
    # "Journal, 2026, DOI: 10.xxxx"; rsc.bst prints no note, so the DOI goes where the pages sit
    if kind == "article" and fields.get("doi") and not fields.get("volume") and not fields.get("pages"):
        fields = {k: v for k, v in fields.items() if k != "note"}
        fields["pages"] = f"DOI: {fields['doi']}"
    if kind == "misc" and fields.get("howpublished") == "Zenodo" and fields.get("doi"):
        fields = dict(fields)
        fields["howpublished"] = f"Zenodo, DOI: {fields['doi']}"
    lines = [f"@{kind}{{{key},"]
    for k, v in fields.items():
        lines.append(f"  {k} = {{{v}}},")
    lines.append("}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()

    # A key entered twice reaches references.bib twice; BibTeX keeps the first, skips the
    # second and reports it only as an ignored error (found 2026-10-11: fathieh2018practical).
    seen, dups = set(), []
    for r in REFS:
        if r[0] in seen:
            dups.append(r[0])
        seen.add(r[0])
    if dups:
        sys.exit(f"REFUSED -- duplicate bibliography keys: {sorted(set(dups))}")

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
            toks = re.sub(r"[{}\\\"'`^~,]", "", name).split()     # "Last, First" form too
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
        # references read through the same source for the same thing share one item
        groups = {}
        for e in partial:
            groups.setdefault(VIA[e[0]], []).append(e[0])
        for text, keys in groups.items():
            fh.write(f"\\item \\cite{{{','.join(keys)}}}: {text}.\n")
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
