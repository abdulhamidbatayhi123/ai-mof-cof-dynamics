#!/bin/bash
# L1, L2 and L7 on dataset v2. Design frozen in PREREG_L1L2L7_v2.md, committed
# before this ran. Order: cheapest and most decisive first (PREREG §5), so a
# shutdown costs the least. Every runner writes after each completed cell and
# resumes by skipping completed cells, so this script is safe to re-run.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8

"$P" -u run_l7_v2.py                >> l7_v2.log 2>&1;              echo "L7_EXIT=$?"
"$P" -u run_l1_v2.py --design both  >> l1_v2.log 2>&1;              echo "L1_EXIT=$?"
"$P" -u analyze_l1_v2.py --no-mde   >> l1_v2_analysis.log 2>&1;     echo "L1A_EXIT=$?"
"$P" -u analyze_l7_v2.py            >> l7_v2_analysis.log 2>&1;     echo "L7A_EXIT=$?"
"$P" -u learning_curve_v2.py        >> learning_curve_v2.log 2>&1;  echo "LC_EXIT=$?"
"$P" -u analyze_lc_v2.py --no-mde   >> learning_curve_v2_analysis.log 2>&1; echo "LCA_EXIT=$?"
"$P" -u run_l2_v2.py                >> l2_v2.log 2>&1;              echo "L2_EXIT=$?"
"$P" -u analyze_l2_v2.py --no-mde   >> l2_v2_analysis.log 2>&1;     echo "L2A_EXIT=$?"
echo V2_RUNGS_DONE
