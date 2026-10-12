# Paper 2 — Registered Report venue comparison

Read 2026-10-12 (Istanbul; the fetch log is UTC 2026-10-11T22:17Z–22:32Z), each rule from
the journal's own live page. No archived copy was used. Metrics: OpenAlex live API, read
2026-10-11T22:29Z (2-year mean citedness, h-index). OpenAlex's APC field is stale, so the
fees below come from each publisher's fee page.

Candidates come from the Center for Open Science's live list of participating journals
(cos.io/initiatives/registered-reports). That list has no chemical-engineering or machine-learning
journal offering RRs. The relevant titles are multidisciplinary, plus Springer's Discover
series. Digital Discovery (RSC), Data-Centric Engineering (CUP) and PeerJ Computer Science's
author instructions do not mention Registered Reports.

| journal | RR rules (live) | Stage-1 length | power rule | fee (live) | 2-yr cit. / h (OpenAlex) | fit for a simulation RR |
|---|---|---|---|---|---|---|
| **Scientific Reports** | nature.com/srep/journal-policies/registered-reports; Stage-1 template on figshare doi:10.6084/m9.figshare.13574714 (file modified 2026-03-07) | no stated cap | "Proposed a priori power levels should be justified" | APC £2,290 / $2,850 / €2,490 | 5.23 / 463 | good: all natural sciences and engineering; judged on rigour, not on how significant the result is; protocol deposited on figshare (embargo possible) |
| **PLOS One** | journals.plos.org/plosone/s/other-article-types#loc-registered-reports; submission-guidelines#loc-registered-reports | no stated cap | none stated | Registered Report Protocol $1,852 + Registered Report Article $1,088 | 3.40 / 597 | good: "all areas of the natural sciences, medicine, and engineering". **The Stage-1 protocol is itself published**: a citable, peer-reviewed article |
| Nature Communications | nature.com/ncomms/submit/registered-reports; guidelines PDF nature.com/documents/ncomms-registered-report-guidelines.pdf; required design table (.docx) | no stated cap | **"0.95 or higher for all proposed hypothesis tests"** | APC £5,490 / $7,350 / €6,150 | 18.33 / 747 | weak: the frozen prereg's MDE is at 80 % power (PREREG_P2 §4.4), so meeting 0.95 would change a frozen quantity. Editors triage on "significance to the field". No funding to pay the APC |
| PNAS Nexus | academic.oup.com/pnasnexus/pages/registered-reports-guidelines; general-instructions | **Stage 1 "should not exceed 3 pages" (~1,600 words)** | 0.9 | not shown without the fee calculator | 7.11 / 50 | weak: our Stage 1 is ~10,200 words |
| Discover Chemical Engineering | link.springer.com/journal/43938/submission-guidelines; Springer "Registered Reports: author guidelines" (Oct 2024 PDF) | no stated cap | **0.9 or higher** | APC £1,190 / $1,690 / €1,390 | 4.92 / 18 (150 works) | best topical fit, least established; 0.9 conflicts with the frozen 80 % |
| Royal Society Open Science | **NOT VERIFIED**: Cloudflare blocks both browsers and the Chrome extension | — | — | — | 4.04 / 130 | strong RR tradition across all sciences; needs a live read before it is considered |
| PCI Registered Reports (free; recommendation, then a PCI-RR-friendly journal) | **NOT VERIFIED**: Anubis bot wall | — | — | — | — | needs a live read |

Springer Nature waivers (Sci Rep, Nat Commun, Discover): automatic only for the lowest-income
countries; other authors "case-by-case ... in cases of financial need", and only if requested
at submission. Türkiye's eligibility was not checked.

Reference points (non-RR): CMAME 9.33 / 321; Chem. Eng. Sci. 4.79 / 298; Comput. Chem. Eng.
5.17 / 202; AIChE J. 4.22 / 281; Digital Discovery 5.83 / 45.

## Cost constraint (author, 2026-10-12): no money for an APC

The author is an unfunded undergraduate, so an article fee is payable only if someone else
pays it. Checked live on 2026-10-12:

- **TÜBİTAK/ULAKBİM EKUAL Read & Publish agreements** (cabim.ulakbim.gov.tr/ekual/e-veri-tabanlari/universiteler/):
  - RSC 2026–2028, Wiley 2026–2028 and OUP 2026–2028 all cover gold and hybrid APCs from a
    quota, but each criteria document requires the corresponding author to be "üniversitelerin
    aktif öğretim kadrosunda" (on a university's active teaching staff). Sources: RSC criteria
    (METU copy of the TÜBİTAK text), `TUBITAK_Wiley_AE_Makale_Fonlama_Kriterleri_2026-2028.pdf`,
    `OUP-AE-Yayin-Destek-Kriterleri.pdf`. **A student corresponding author is not eligible.**
  - The Springer Nature 2024–2026 agreement guide routes only hybrid journals, so it does not
    reach the fully open-access Scientific Reports.
  - None of these publishers runs a Registered Report format in this field, except PNAS Nexus
    (OUP), which has the 3-page Stage-1 cap.
- **PLOS Publication Fee Assistance**: case-by-case, for "authors unable to pay all or part"
  who show financial need. It must be applied for at submission, with a decision "usually ...
  within 10 business days" that editors never see. Research4Life eligibility for Türkiye was not
  verified (research4life.org returns 403 to automated reads).
- **Springer Nature**: discretionary waiver "case-by-case ... in cases of financial need",
  requested at submission only.
- **PCI Registered Reports → Peer Community Journal**: "The entire PCI and Peer Community
  Journal process is free for any user" (peercommunityin.org). PCJ is diamond open access,
  "free for both authors and readers", publishes PCI-RR-recommended Registered Reports, and
  covers "life sciences ... physical sciences, social sciences, and humanities"
  (peercommunityjournal.org/page/about). OpenAlex: 2-yr 3.70, h 24, 644 works, in DOAJ.
  **PCI RR's own scope page (rr.peercommunityin.org) could not be read**: an Anubis bot wall
  blocks automated reads, and it has to be read before submission.

## Top-tier check (author, 2026-10-12: "the best journal", no Q2/Q3; a YTÜ professor can be corresponding author)

- Springer Nature–TÜBİTAK 2024–2026 licence table (`Springer_nature_Lisans_Anlasmasi_2024-2026.xlsx`):
  the supported articles are only those in "Hybrid açık erişimli dergilerden Q1 ve Q2 grubuna
  giren dergiler". **Nature Communications (gold) is not covered, even with a faculty
  corresponding author.**
- Nature Computational Science (OpenAlex 2-yr 11.37, h 75) and Nature Chemical Engineering
  (12.04, h 41) are subscription/hybrid journals, so closed-access publication is free. Their
  live content-type and submission-guideline pages list Article, Analysis, Brief Communication
  and Resource, and **no Registered Report**.
- So the Registered Report format and a free top-tier field journal do not coexist for this
  paper. The frozen prereg already resolves this (PREREG_P2, "Registered Report timing"): the
  grid runs after Stage-1 IPA, "or, if no journal grants it within six months of the freeze"
  (freeze 2026-10-11, so 2027-04-11) "after a dated amendment saying so — in which case the
  paper is reported as a pre-registered study".
- Nature Communications' 0.95-power rule against the frozen design: the frozen MDE is
  0.25 decade at 80 % power (SD 0.089 decade, PREREG §4.4). At 95 % power the same
  estimator resolves (1.96 + 1.645) × 0.089 ≈ 0.32 decade. Changing the quoted MDE would
  change a frozen number, which the prereg allows only as a dated amendment made at a Stage-1
  reviewer's request.

## Decision (author, 2026-10-12): Nature Communications Stage 1 now; free top journals as the fallback

1. **Submit Stage 1 to Nature Communications.** Its Article page says "we do not consider
   pre-submission enquiries", so the 0.95-power point is raised in the Stage-1 cover letter.
   The manuscript states the frozen 80 % MDE and the derived 95 % figures, and offers a
   reviewer-requested amendment (raising the replicate count before any grid run). The APC
   (£5,490 / $7,350 / €6,150) is due only at final acceptance; it needs a payer (a
   professor's grant or a future lab) or withdrawal before then.
2. **If Nature Communications declines, or no IPA arrives by 2027-04-11**, the frozen
   prereg's clause applies: a dated amendment, the grid is run, and the paper is reported as
   a pre-registered study and sent to Nature Computational Science or Nature Chemical
   Engineering (free, closed access), then AIChE J. / Chem. Eng. Sci.

Stage-1 package (built 2026-10-12): `paper2/stage1.tex` / `.pdf`,
`paper2/submission/stage1_design_table.docx` (`make_stage1_table_docx.py`),
`check_stage1_p2.py` → `audit_2026-10-12/stage1_checks.json`, `audit_references_p2.py` →
`audit_2026-10-12/reference_audit_p2.json`, `p2_operating_characteristics.py` →
`results/p2_operating_characteristics.json`. The cover letter is kept private (`outreach/`).

## Earlier recommendation (superseded by the cost constraint and the decision above)

**Scientific Reports**:
1. It is the only venue that is verified, well cited (2-yr 5.23, above PLOS One, RSOS and
   Chem. Eng. Sci.), and compatible with the frozen design: it requires the power level to be
   justified, not 0.9 or 0.95, so the frozen 80 %-power MDE of 0.25 decade stands with its
   justification.
2. It has no Stage-1 length cap, so the full methods stay in the main text.
3. It publishes the result whichever way the map falls, which is the point of the RR.

**Fallback 1: PLOS One.** Same compatibility, a lower fee in two parts, and the Stage-1 protocol
is published as its own citable article (useful for an application file). It is cited less.
**Fallback 2: RSOS or PCI RR**, once someone can read their live pages.
**Not recommended:** Nature Communications (the 0.95 power rule conflicts with the frozen
design; $7,350 APC unfunded) and PNAS Nexus (3-page Stage 1).
