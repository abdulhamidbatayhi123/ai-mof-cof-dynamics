# Real water-harvesting adsorbents in the design-v2 parameter space

Compiled 2026-10-04 for a referee figure/table. The machine-readable version, with a quote or figure-reading note for every value, is `research/water_mof_parameters.json`. Every DOI below was checked against the Crossref API; the title and authors Crossref returned match the citation.

Conversions: mol/kg = (g/g) / 0.0180153; mol/kg = (cm3 STP/g) / 22.414. Literature heats are positive magnitudes, so our dH_ads = -Qst. "Henry fraction" = uptake just before the step divided by uptake near p/p0 = 0.9. It is an estimate, not a fitted value.

## Summary table

| MOF | RH_step (p/p0) [T] | q_sat (mol/kg) | -dH_ads (kJ/mol) | Henry fraction (est.) |
|---|---|---|---|---|
| MOF-303 | 0.12 inflection [30 C] (H19); 0.15 inflection [T not stated] (F18) | 24.5 at 0.9 [fig, H19]; 26.6 stated max (F18) | 52 (H19) | ~0.17 (fig, low) |
| MOF-801-P | ~0.07 midpoint, step 0.05-0.10 [25 C] (Fu14) | 20.0 at 0.9 (Fu14) | ~60 (Fu14) | ~0.07 (fig, low) |
| CAU-10-H | 0.19-0.22 [characteristic curve, 3-30 C P0] (S21) | 18.0 at 0.8 (S21); 18.6 max powder (Fr16) | >50 plateau, 56 low loading (Fr16); 61+/-3 at step (S21) | <=0.03 (S21) |
| Al-fumarate (A520) | ~0.265 midpoint [30 C] (fig, H19); 0.25 inflection [30 C, coating] (L20) | 23.0 at 0.9 (fig, H19) | 52.2+/-1.0 (L20); 50-54 joint range (H19) | ~0.05 (fig, low) |
| MIL-160(Al) | ~0.085 midpoint [20 C] (fig, S21b); alpha 0.09 [20 C] (A26); 0.08 [25 C] (Le19, secondary) | 18.9 max (S21b); 24.1 plateau [20 C] (A26) | 49-52 (S21b) | ~0.06 (S21b) |
| Co2Cl2(BTDD) | 0.28 [25 C] (R17) | 53.7 at 94% RH (R17) | 55 at zero coverage, 45.8 during pore filling (R17) | ~0.19 (fig, medium) |

"fig" means the value was read by eye from a rendered figure of the open-access PDF, to about +/-0.01-0.02 in p/p0 and +/-10-20 cm3/g in uptake.

## Inside or outside our design-v2 ranges

| Parameter (range) | Inside | Edge | Outside |
|---|---|---|---|
| RH_step (0.08-0.45) | MOF-303, CAU-10-H, Al-fum, Co2Cl2(BTDD) | MIL-160 (0.08-0.09, at the lower edge) | MOF-801-P (~0.07, just below) |
| q_max (8-30 mol/kg) | MOF-303, MOF-801, CAU-10-H, Al-fum, MIL-160 | none | **Co2Cl2(BTDD) (53.7)** |
| dH_ads (-60 to -38 kJ/mol) | MOF-303, Al-fum, MIL-160, Co2Cl2(BTDD), CAU-10-H (Fr16 value) | MOF-801-P (~-60) | CAU-10-H with the S21 step value (-61+/-3), marginally |
| Henry fraction (0.03-0.25) | MOF-303, MOF-801, Al-fum, MIL-160, Co2Cl2(BTDD) | CAU-10-H (<=0.03) | none clearly |

The cooperativity exponent, particle diameter, particle density and bed porosity are not intrinsic MOF properties. They depend on the shaped body and the bed, so they were not sourced.

## Sources (key, DOI, Crossref-verified)

- **H19**: Hanikel, Prevot, Fathieh, Kapustin, Lyu, Wang, Diercks, Glover, Yaghi. "Rapid Cycling and Exceptional Yield in a Metal-Organic Framework Water Harvester." *ACS Cent. Sci.* 2019, 5, 1699-1706. 10.1021/acscentsci.9b00745. Open access. MOF-303 values are in the text and Fig. 1a; Al-fumarate (Basolite A520) values are in Fig. 2. All isotherms were measured at 30 C.
- **F18**: Fathieh, Kalmutzki, Kapustin, Waller, Yang, Yaghi. "Practical water production from desert air." *Sci. Adv.* 2018, 4, eaat3198. 10.1126/sciadv.aat3198. Open access (PMC5993474).
- **Fu14**: Furukawa, Gandara, Zhang, Jiang, Queen, Hudson, Yaghi. "Water Adsorption in Porous Metal-Organic Frameworks and Related Materials." *J. Am. Chem. Soc.* 2014, 136, 4369-4381. 10.1021/ja500330a. The publisher PDF was read from the Yaghi group website. Values are from Fig. 6a (25 C), p. 4375, and Section 4.
- **S21**: Solovyeva, Shkatulov, Gordeeva, Fedorova, Krieger, Aristov. "Water Vapor Adsorption on CAU-10-X: Effect of Functional Groups..." *Langmuir* 2021, 37, 693-702. 10.1021/acs.langmuir.0c02729. Open access (PMC7880571). The isotherm is a characteristic curve built from isobars.
- **Fr16**: Frohlich et al. "Water adsorption behaviour of CAU-10-H: a thorough investigation of its structure-property relationships." *J. Mater. Chem. A* 2016, 4, 11859-11869. 10.1039/c6ta01757f. Open access under CC BY-NC. Values are on p. 11861 and in the heat-of-adsorption section with Fig. 10.
- **L20**: Laurenz, Fuldner, Schnabel, Schmitz. "A Novel Approach for the Determination of Sorption Equilibria and Sorption Enthalpy Used for MOF Aluminium Fumarate with Water." *Energies* 2020, 13, 3003. 10.3390/en13113003. Only the abstract was read. The sample is a binder-based coating.
- **S21b**: Solovyeva, Krivosheeva, Gordeeva, Aristov. "MIL-160 as an Adsorbent for Atmospheric Water Harvesting." *Energies* 2021, 14, 3586. 10.3390/en14123586. Open access. Values are from Section 3.2, Figs. 4-5, and the Conclusions.
- **A26**: Aumond, Bonneau, Daniel, Perbet, Meunier, Farrusseng. "Adsorption Performances of Water-Stable MIL-160(Al) at Scale..." *ACS Omega* 2026, 11, 16294-16299. 10.1021/acsomega.5c11973. Open access (PMC13000597). Values are from Table 1 and Fig. 1a (20 C).
- **Le19**: Lenzen et al. "A metal-organic framework for efficient water-based ultra-low-temperature-driven cooling." *Nat. Commun.* 2019, 10, 3025. 10.1038/s41467-019-10960-0. Used only as a **secondary** statement about MIL-160; it cites Permyakova 2017 and Cadiau 2015.
- **R17**: Rieth, Yang, Wang, Dinca. "Record Atmospheric Fresh Water Capture and Heat Transfer with a Material Operating at the Water Uptake Reversibility Limit." *ACS Cent. Sci.* 2017, 3, 668-672. 10.1021/acscentsci.7b00186. Open access (PMC5492259). Values are from Fig. 2A (298 K) and Fig. 3A, plus the text. Co2Cl2(BTDD) is compound "2" in this paper.

## Conflicts and caveats (kept, not resolved)

1. **MOF-303 step**: H19 gives an inflection of about 0.12 at 30 C, and F18 gives 0.15 with no temperature in the sentence. The two papers used different samples (F18 Fig. 4B is MOF-303 blended with graphite). Saturation also differs: 0.48 g/g is F18's stated maximum, while H19 Fig. 1a shows about 0.44 g/g at p/p0 = 0.9.
2. **CAU-10-H heat**: Fr16 reports about 56 kJ/mol at low loading and a plateau slightly above 50, calculated from three literature isotherms. S21 reports a peak of 61+/-3 at the step and about 52 at the start and end. The step position comes only from S21, which uses isobars and a Polanyi characteristic curve. The original Reinsch 2013 and Frohlich 2014 isotherms were not accessible.
3. **MIL-160 capacity**: S21b gives 0.34 g/g (18.9 mol/kg), while A26 gives 24.1 mmol/g (0.434 g/g) at 20 C for a scaled-up batch, and A26 says the rise above 95% RH is intercrystalline. The step position agrees across sources (0.08-0.09). The original MIL-160 papers (Cadiau 2015, Permyakova 2017) are paywalled and were not read.
4. **Al-fumarate step**: the H19 powder (Basolite A520) at 30 C reads about 0.26-0.27 from the figure, and the L20 coating at 30 C has an inflection of 0.25. These are consistent. L20 also shows the step moving with temperature: 0.28 at 40 C and 0.33 at 60 C. H19's isotherm shows a small hysteresis. The H19 heat is a joint 50-54 kJ/mol range for MOF-303, Al-fumarate and SAPO-34 together.
5. **MOF-801 heat**: Fu14 gives about 60 kJ/mol, which sits exactly at our -60 bound. Fu14 also shows that the -P powder holds about 1.3x more than the -SC single crystals (36 vs 28 wt%) and attributes this to missing-linker defects.
6. **Co2Cl2(BTDD)** is the clear outlier. Its capacity of 0.968 g/g (53.7 mol/kg) is about 1.8x our q_max ceiling, and its pre-step uptake of about 0.18 g/g (about 10 mol/kg) is unusually large in absolute terms. The heat falls from 55 to 45.8 kJ/mol during pore filling.
7. **Step definitions differ**: sources variously report an "inflection", an alpha (half of total capacity), or a midpoint read from a figure. Our RH_step is the step centre of the cooperative term, so these are comparable only to within about +/-0.02.

## Not sourced, and what was tried

- Cadiau 2015 (10.1002/adma.201502418) and Permyakova 2017 (10.1002/cssc.201700164): Unpaywall, Semantic Scholar and Europe PMC all report them closed, and Wiley returned 403.
- Reinsch 2013 (10.1021/cm3025445): the only repository copy shows "No access".
- Frohlich 2014 Dalton (10.1039/c4dt02264e) and Jeremias 2014 RSC Adv. (10.1039/c4ra03794d) are open access at RSC, but pubs.rsc.org returned 403 to automated fetches.
- Full text of Laurenz 2020: mdpi.com returned 403, so only the abstract was used.
- No source gives an explicit number for the below-step uptake of MOF-303, MOF-801-P or Al-fumarate. Those Henry fractions are figure readings with low confidence.
- No preprint (ChemRxiv) sources were used.
