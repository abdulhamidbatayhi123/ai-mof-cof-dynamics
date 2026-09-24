# citations

The build gate itself is clean: all 40 `\cite` commands resolve to 47 distinct keys, every one of which is present in references.bib, so there is no dangling citation and nothing breaks the build. The honesty gate is not clean: the manuscript twice promises a list of references cited through a secondary source and that list does not exist anywhere in the document, two of the six emitted PARTIAL entries are cited with no read-through flag at all, and defect B62 has recurred — thirteen given names in references.bib appear nowhere in CITATIONS.md, the audit records, or any other file in the repository. Separately, the Glueckauf 1955 DOI in the bibliography does not match the one CITATIONS.md recorded, four VERIFIED weighting-scheme references never reached references.py at all while the manuscript names their methods, and five bib entries are dead weight because the generator's gate only checks the cited-but-missing direction.

## 1. [blocking] paper/manuscript.tex:207-208, 949-951

**What.** Line 207 states: "Section~\ref{sec:reproducibility} lists every reference cited through a secondary source rather than read at the primary." Section sec:reproducibility contains no such list. Its entire treatment is the closing sentence of the \paragraph{Citations.} block at lines 949-951: "References that could not be retrieved at the primary and are cited through a verified secondary source are listed as such." That sentence asserts the existence of a list and is itself the only thing present. `grep -n "secondary" manuscript.tex` returns exactly three hits: 207, 858 (the Klinkenberg entry) and 951. Nothing enumerates danckwerts1953continuous, glueckauf1955theory, klinkenberg1948numerical, anzelius1926uber, schumann1929heat, dodo2000model.

**Why.** It is a false statement about the paper's own contents, made in the section whose subject is auditing the paper's own reading, and cross-referenced from the verification section. A referee who follows the \ref finds nothing there. The .bib does carry `% [PARTIAL -- cited through a verified secondary source]` comment lines (references.bib lines 424, 440, 465, 494, 508, 521), but BibTeX comments never reach the rendered PDF, so no reader ever sees them.

**Fix.** Add an explicit itemised list to sec:reproducibility naming all six emitted PARTIAL entries and, for each, the verified secondary source the claim rests on: Danckwerts 1953 through Pearson 1959; Glueckauf 1955 through Perry's Sec. 16 and Cruz et al. 2006; Klinkenberg 1948 through Seader, Henley & Roper; Anzelius 1926 and Schumann 1929 through Perry's handbook; Do & Do 2000 through Buttersack 2019. Generate it from references.py rather than typing it, so the list cannot drift from the emitted set — the same discipline the numbers macros already enforce.

## 2. [blocking] paper/references.bib:151, 293, 527, 541, 598, 610, 666

**What.** Thirteen given names in author fields appear in no project record. A repo-wide search for `Yizheng|Jinshuai|Cosmin|Sadegh|Xiaoying|Timon|Yinghua|Ariana|Aleksandr|Duong|Giorgio|Zhiling|Ilja|Douglas` returns exactly two files: paper/references.bib and paper/references.py. They are absent from CITATIONS.md, audit_2026-08-30/citation_verification.md, literature_review_raw.json and every PREREG. The offending lines: 151 `{Yizheng Wang and Jia Sun and Jinshuai Bai and Cosmin Anitescu and Mohammad Sadegh Eshaghi and Xiaoying Zhuang and Timon Rabczuk and Yinghua Liu}` (CITATIONS.md:435 records only "Wang, Sun, Bai, Anitescu, Eshaghi, Zhuang, Rabczuk & Liu"); 293 `{Ariana Mendible and Steven L. Brunton and Aleksandr Y. Aravkin ...}` (CITATIONS.md:412 records only surnames); 527 and 541 `{Duong D. Do and Ha D. Do}` / `{Duong D. Do and S. Junpirom and Ha D. Do}` (CITATIONS.md:560-561 record only "Do & Do" and "Do, Junpirom & Do"); 598 `{M. Douglas LeVan and Giorgio Carta}` and 610 `... M. Douglas LeVan ...` (CITATIONS.md:521, 485 record only "LeVan & Carta" and "Knox, Ebner, LeVan, Coker & Ritter"); 666 `... Zhiling Zheng ... J. Ilja Siepmann ...` (CITATIONS.md:515 records only surnames).

**Why.** This is defect B62 recurring, and references.py's own docstring (lines 18-23) forbids exactly it: "NEVER EXPAND AN INITIAL ... Turning it into 'Eugen Glueckauf' is an unverified assertion about a real person's name ... Use the form the verification pass actually recorded, or 'and others'." These names may well be correct, but nothing in the repository shows they were fetched, so the file violates the rule it exists to enforce, in a paper whose citation gate is a selling point. Contrast the entries where the discipline held: ogata1961solution keeps `R. B. Banks` rather than expanding to "Robert" precisely because CITATIONS.md:551 recorded the title-page form, and klinkenberg's `Adriaan` is legitimate because audit_2026-08-30/citation_verification.md:209 recorded it from Crossref.

**Fix.** For each of the seven entries, either re-fetch the record and write the recorded author string into CITATIONS.md so the bib has provenance, or fall back to the recorded form — surname-only, or first author plus `and others`, as rohrer2021loss and krass2025mofsimbench already do. Then add a check to references.py that fails when a bib author token does not occur in CITATIONS.md or the audit records, so B62 cannot recur a third time.

## 3. [major] paper/references.py:313

**What.** The DOI emitted for glueckauf1955theory is `10.1039/TF9555101540` (references.py:313, reaching references.bib:451). CITATIONS.md:552 — the only place the record was ever written down — gives `DOI 10.1039/TF9551501540`. The two strings differ by a transposition in the middle: `TF955|15|01540` in the ledger versus `TF955|51|01540` in the bibliography.

**Why.** The ledger is the record of what was verified; the bibliography must not carry an identifier the verification pass never recorded. This is the same failure class as B42 (an identifier that resolves to the wrong thing) on an entry that is already PARTIAL and BLOCKED at the primary, so nobody can adjudicate it by opening the paper. One of the two strings is a dead or wrong identifier and the project cannot currently say which.

**Fix.** Re-resolve the DOI against Crossref and write the fetched string into CITATIONS.md:552 and references.py:313 so they agree. Note that only the references.py form is consistent with the RSC legacy pattern TF + 9 + year(55) + volume(51) + page(01540) — the ledger's `TF9551501540` would encode volume 15, which contradicts the volume 51 recorded on the same line — so the likely correction is to the ledger, but it must be fetched, not inferred.

## 4. [major] paper/manuscript.tex:337-338

**What.** `\cite{glueckauf1947theory,glueckauf1955theory}` supports "it is derived from particle size through a Glueckauf relation". glueckauf1955theory is emitted as PARTIAL with allow_partial=True (references.py:308-315), and CITATIONS.md:552 records it as "**BLOCKED on the primary** ... The factor 15 has never been read from Glueckauf's own text." The manuscript flags no other reference this way at this point and gives the reader no indication that the 1955 primary was never retrieved.

**Why.** The manuscript's \paragraph{What we read, and what we read through.} (lines 216-221) flags Anzelius, Schumann and Danckwerts by name, so a reader reasonably infers that everything not flagged there was read at the primary. Glueckauf 1955 was not. It also carries the live B55 attribution risk — Cruz et al. attribute the plain 15-factor LDF to Glueckauf & Coates (1947) and label a different expression as the 1955 result — which the unflagged citation hides.

**Fix.** Add glueckauf1955theory to the sec:reproducibility list required by the first finding, and add one clause at line 338 in the style already used at line 216: state that the 1955 paper is closed at the publisher, that the factor 15 is verified through Perry's Sec. 16 and Cruz et al. (2006), and that the 1947 companion is cited for that reason.

## 5. [major] paper/manuscript.tex:226

**What.** `\cite{dodo2000model}` supports "a dual-term form \emph{in the spirit of} Do and Do". dodo2000model is emitted as PARTIAL with allow_partial=True (references.py:350-357). CITATIONS.md:560 records: "**PARTIAL because the Carbon 2000 paper itself was not retrievable** (Elsevier closed; null abstract on Crossref, OpenAlex and Semantic Scholar); the functional form was verified from Buttersack's open-access reproduction." The manuscript discusses the B56 correction at length (lines 236-247) and cites buttersack2019modeling at line 242, but only for the Sips term's zero slope at the origin — never to say that the Do--Do functional form itself was read out of Buttersack rather than out of Carbon.

**Why.** The whole of Section 3.1 rests on what Do & Do's two-term construction actually is, and that was taken from a third party who is, per CITATIONS.md:562, "mildly adversarial" to the model. The reader is told the paper corrected its own naming of the form (B56) but not that it never read the form's source, which is the more consequential omission.

**Fix.** Add dodo2000model to the sec:reproducibility list, and extend the sentence at line 242 so that buttersack2019modeling is credited as the source through which the Do--Do form was read, not only as support for the zero-slope property — with a clause noting Buttersack proposes a competing isotherm so his transcription is not an endorsement.

## 6. [major] paper/manuscript.tex:517-521

**What.** The L4 design paragraph names four methods from the literature with zero citations: "fixed weights over four decades, gradient-norm balancing at three target ratios, neural-tangent-kernel weighting, and self-adaptive per-point weights". `grep -c "Perdikaris\|McClenny\|Rathore" paper/references.py` returns 0 — none of the four sources reached the generator, so none are in references.bib and none can be cited. All four are recorded VERIFIED in CITATIONS.md lines 398-401 (Wang, Teng & Perdikaris, SISC 43(5):A3055 2021; Wang, Yu & Perdikaris, JCP 449:110768 2022; McClenny & Braga-Neto, JCP 474:111722 2023; Rathore et al., ICML 2024), and PREREG_L4b_v2.md lines 52-54 and 88 names each one against the arm that implements it.

**Why.** Four named methods presented as the paper's own design vocabulary with no attribution is the plainest form of missing citation a referee looks for, and it is gratuitous here: the verification work is already done and sitting in the ledger. It also breaks the chain between the pre-registration, which attributes each arm, and the manuscript, which does not — weakening the pre-registration's evidential value, the thing this paper trades on.

**Fix.** Add the four VERIFIED entries from CITATIONS.md:398-401 to references.py with the author strings recorded there, and cite them at lines 519-520 against the arms they belong to: gradient-norm balancing to Wang, Teng & Perdikaris (2021); NTK weighting to Wang, Yu & Perdikaris (2022) with the stated trace-approximation caveat from CITATIONS.md:399; self-adaptive weights to McClenny & Braga-Neto (2023); and Rathore et al. (2024) wherever the Adam-then-L-BFGS polish is described.

## 7. [major] paper/manuscript.tex:563

**What.** "it is the direction the theory predicts, and it is the first measurement of what the escape is actually worth on a physical problem rather than in an approximation bound." A bare priority claim, with no citation and no falsification search recorded anywhere in CITATIONS.md. The ledger's one documented falsification question (CITATIONS.md:467-468) is about the two-landmark time reparameterisation, not about FNO-versus-DeepONet on a physical problem.

**Why.** Working rule 8 says nothing is cited until fetched; the symmetric obligation for a "first" claim is that a search was run and recorded, and none was. The project has already been burned by exactly this: A23 was a broad novelty claim falsified by papers that existed, and the Introduction at lines 104-108 handles its surviving novelty claim correctly by citing the papers that would otherwise falsify it. Line 563 gets none of that treatment, and the FNO-versus-DeepONet comparison on physical problems is a crowded literature.

**Fix.** Either run and record a falsification search in CITATIONS.md and cite the near-misses alongside the claim, in the same form as lines 104-108; or narrow the sentence to what the evidence supports — e.g. "we measure what the escape is worth on this problem" — and drop "first".

## 8. [major] paper/manuscript.tex:720-721

**What.** "Piecewise landmark registration --- a monotone warp built by interpolating between identified landmark times --- is the standard alignment method in functional data analysis \cite{kneip1992statistical,ramsay1998curve}". CITATIONS.md:460 records ramsay1998curve as the opposite branch: "**B38 remains correct** that their *method* is the landmark-free branch, and B38 itself already allowed citing them as the landmark-free contrast". references.py:273-274 repeats it: "The landmark-FREE branch, cited as the canonical curve-registration reference and as the contrast." Separately, CITATIONS.md:475-476 grounds the word "standard" in software — "shipping in `R fda::landmarkreg` and `scikit-fda`'s `landmark_registration`" — not in either cited paper.

**Why.** The ledger records this source as not supporting the proposition it is cited for. Ramsay & Li is being used as evidence that landmark registration is standard when the project's own verification says its method is the landmark-free alternative, and it is being cited as the contrast nowhere in the manuscript. A functional-data referee will know the distinction on sight, which is precisely why B38 exists.

**Fix.** Cite kneip1992statistical alone for landmark registration, and recast ramsay1998curve in the contrast role the ledger assigns it — one clause noting the landmark-free branch, e.g. "with a landmark-free alternative in Ramsay and Li". If the word "standard" is kept, ground it where the ledger grounds it, on the FDA implementations.

## 9. [minor] paper/references.bib:123, 163, 307, 334, 348

**What.** Five entries are emitted but never cited: abueidda2025deepokan (line 123), kiyani2025optimizing (163), gowrachari2025cross (307), ohlberger2013nonlinear (334), greif2019decay (348). references.py's gate at lines 497-500 checks only the opposite direction — `uncited_in_bib = sorted(cited - {e[0] for e in emitted})` and exits 1 on cited-but-missing keys — so nothing detects an emitted entry no \cite reaches. Two of the five are load-bearing elsewhere: RETRACTIONS.md:79 records that retraction A12 rests on abueidda2025deepokan, and RETRACTIONS.md:144 (B45) states A12 "stands, on two references instead of one", the second being shukla2024comprehensive, which is cited.

**Why.** With elsarticle-num the uncited entries silently vanish from the printed reference list, so this is bibliography hygiene rather than a build failure. But the Abueidda case is more than hygiene: the L3 section (lines 488-502) argues the KAN prior art and never names DeepOKAN, while the project's own retraction ledger says one of the two papers A12 rests on is Abueidda. A referee reading the corrections section and then the reference list will not find it.

**Fix.** Add the reverse check to references.py — report, and optionally fail, when an emitted key is cited by no \cite. Then for each of the five, decide deliberately: cite abueidda2025deepokan where A12's narrowed novelty claim is discussed, cite kiyani2025optimizing in the split-literature paragraph at lines 488-502 for the finding CITATIONS.md:436 actually supports, and drop gowrachari2025cross, ohlberger2013nonlinear and greif2019decay from REFS unless a citation is added — CITATIONS.md:449 already conditions greif2019decay on wave problems being discussed, and they are not.

## 10. [minor] paper/manuscript.tex:462, 733

**What.** Two assertions about the literature carry the word "textbook" and no citation. Line 462: "That the \emph{optimal} capacity grows with the material count is the textbook signature of a data-limited rather than a representation-limited regime". Line 733: "The textbook remedy for a transport-dominated \(n\)-width is to factor the front position out before projecting."

**Why.** "Textbook" is a claim about what the literature established, and under working rule 8 an uncited one is exactly the sort the paper's own gate exists to catch. Line 733 is the weaker case because reiss2018shifted is cited twenty lines earlier in the same section, but line 462 has no nearby support at all.

**Fix.** Attach a citation to each, or reword to the paper's own voice. Line 733 can carry \cite{reiss2018shifted} directly. Line 462 needs either a source or a rephrasing that does not assert what textbooks say.

## 11. [minor] paper/manuscript.tex:880

**What.** "and Perry's handbook presents that form as a \emph{lower bound} for \emph{nonporous} particles, noting that the leading coefficient rises to as much as \(20/\varepsilon\)" — Perry's is named and a specific quantitative claim is attributed to it, with no \cite. levan2019adsorption is cited at lines 204 and 274 but not here.

**Why.** A named source carrying a numeric claim with no key is the pattern that produced B43. The sentence is also the load-bearing half of the dispersion-closure limitation, and CITATIONS.md:517 records the 20/ε figure and the strongly-adsorbed-species caveat as coming from Perry's Table 16-10.

**Fix.** Add \cite{levan2019adsorption} at line 880 after "Perry's handbook".

## 12. [minor] paper/manuscript.tex:216-218

**What.** "the \(J\)-function was verified through Perry's handbook \cite{levan2019adsorption} rather than from either original". CITATIONS.md:558 records a further link the sentence does not disclose: "Perry's attributes the **J(s,t) integral definition** to **Hiester & Vermeulen, *Chem. Eng. Prog.* 48:505 (1952)** — that journal is not in Crossref, the reference is **UNVERIFIED, and it may not be cited**." The ledger entry for levan2019adsorption (CITATIONS.md:521) records verification of the simple-wave/shock/constant-pattern claim, not of the J-function's functional form.

**Why.** A two-step chain — original unread, Perry's read, Perry's own attribution unverifiable — is presented as a one-step read-through. CITATIONS.md:559 gives the guidance the sentence sidesteps: "If L0's verification rests on the exact functional form of J, one of the two originals must be obtained; otherwise phrase as *'the classical Anzelius–Schumann solution'* without quoting equation numbers." Table tab:l0 does check the LDF term against Anzelius--Schumann, so L0's verification does rest on the form.

**Fix.** State the chain: that Perry's carries the J(s,t) definition and itself attributes it to a 1952 source the project could not verify, so the check rests on Perry's transcription. Keep the existing avoidance of equation numbers.

## 13. [minor] paper/references.py:191-200

**What.** The refusal is `papapicco2022nnspod` (state P, allow_partial=False), the only entry in REFS that is neither VERIFIED nor a PARTIAL marked citable, so it is the one entry printed as REFUSED on every run. The manuscript does not cite it — it appears in none of the 47 \cite keys — so there is no violation. But the consequence is unclosed: CITATIONS.md:462 flags it as a priority risk, "**Predates Zorawski et al. by two years**, so 'the neural sPOD' must not be attributed to Zorawski", and the warp section's prior-art paragraph at manuscript.tex:709-716 opens "Aligning multiple transports is \textbf{not new}, and none of it is claimed here" and then lists zorawski2024neural among "several later works" with the earliest neural-sPOD paper absent.

**Why.** The paragraph is a completeness claim about prior art in a section built to pre-empt a novelty challenge, and the ledger records a paper that belongs in it and cannot be cited because it was retrieved only from a Crossref query listing. The manuscript never names "the neural sPOD", so nothing is currently misattributed — the risk is the omission, not an error.

**Fix.** Fetch the Papapicco record directly from Crossref works/10.1016/j.cma.2022.114687 to confirm volume, pages and article number, promote it to VERIFIED in CITATIONS.md and references.py, and add it to the \cite group at manuscript.tex:715. Until then leave the refusal in place. While editing that line, consider CITATIONS.md:457's instruction to describe zorawski2024neural as a non-peer-reviewed proceedings item.

