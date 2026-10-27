# refs/

Only `Lassitter2024_fig10_digitised.csv` is tracked here. Third-party figures and PDFs used
to make it are kept locally and are not in the repository.

`Lassitter2024_fig10_digitised.csv` is a measurement of Fig. 10 of Lassitter et al.,
*Chem. Eng. Sci.* 285:119430 (2024), "Experimental Breakthrough Curve (points) and COMSOL
model (line)" for a MOF-303 packed bed. The operating conditions are in their SI Table S8.
It was produced by `digitise_lassitter.py` from a PNG of the figure taken from the
published PDF. The axis limits come from the plot frame (0 to 600 min, 0 to 35 % RH),
the model line is picked by colour, and the open markers are classified as squares or
circles by whether their bounding-box corners are inked. Nothing is fitted.

Columns: `series` (`effluent_circle`, 37 points; `inlet_square`, 39 points;
`comsol_model_line`, 625 points), `t_min`, `rh_percent` and `note` (marker area and
corner ink, for the markers). `compare_lassitter.py` and `anchor_strong_sites.py` read it.
The values are a digitisation of a printed figure and carry its resolution, about one
pixel in each axis.
