> # ⚠ WITHDRAWN — DO NOT USE, DO NOT CITE, DO NOT COPY INTO A MANUSCRIPT
>
> Withdrawn 2026-08-30 (audit finding B8). Retained only as provenance.
>
> This file argues for an architecture choice the project's own measurements
> then contradicted. Specific defects:
>
> | claim in this file | status |
> |---|---|
> | trees/MLPs included "strictly as strawman baselines" | **inverts the finding.** Gradient-boosted trees are the STRONGEST data-driven arm (0.0485) and the reference every later rung is measured against. Protocol §3 forbids strawman comparisons. |
> | "(see Section X)" | a literal unresolved placeholder |
> | "the MTZ propagates as a highly localized, sharp shock front" | **contradicted by §6c** — a Type V isotherm gives a fast spreading Henry wave AND a slow cooperative shock, two waves whose separation varies 40x |
> | "localized RBF bases... sharply resolve the shock without oscillation" | **L3** — RBF-KAN is significantly worse than the MLP on held-out materials at every budget |
> | "the localized KAN edges can be extracted... symbolically extract kinetic rate equations" | **no implementation exists anywhere in this repository** |
> | "we benchmark against... FNO, and WNO" | **neither was ever run** (audit §5A(i)); the WNO that existed was a dilated CNN (**A9**) |
> | "definitively prove that localized, physics-informed operator networks are the optimal architecture" | the measurement says the opposite |
>
> The interpretability story the project actually earned is better and is real:
> the equilibrium object is recoverable from an observable isotherm fingerprint
> (R² = 0.93–0.96) while the kinetic coefficient is not (R² = −0.61). See the
> IDENTIFIABILITY section of `03_LADDER_PROTOCOL.md`.

# 2. Methodology & Architecture Justification

To rigorously benchmark the capabilities of our Foundation Digital Twin, it is imperative to construct a clear comparative taxonomy of deep learning architectures. The selection of our core models—the Physics-Informed Kolmogorov-Arnold Network (PIKAN) and the Fourier Neural Operator (FNO)—was explicitly motivated by the underlying physics of MOF/COF multiphysics adsorption. Below, we justify the selection of our novel architectures against the theoretical limitations of both standard machine learning and emerging neural operators.

### 2.1 The Failure of the Interpolative Baseline (Data-Driven ML)
Standard data-driven models, including Multi-Layer Perceptrons (MLPs), XGBoost, and Random Forests, operate strictly by interpolating within the convex hull of their training data. In our benchmarking (see Section X), these architectures achieved near-zero error on training regimes (memorization) but suffered catastrophic error explosions (extrapolation failure) when querying unseen temporal domains or novel material properties. They lack intrinsic knowledge of Fickian diffusion or thermodynamic mass conservation. Consequently, we include these strictly as "strawman" baselines to establish the absolute necessity of physics-informed constraints in chemical engineering tasks.

### 2.2 Global Operators: Fourier Neural Operator (FNO)
To achieve real-time "Digital Twin" simulation, we require a model capable of mapping continuous parametric inputs (e.g., weather profiles and MOF kinetics) to the entire spatiotemporal adsorption field. 
**Why FNO?** The Fourier Neural Operator operates in the frequency domain, making it discretization-invariant and exceptionally computationally efficient ($O(n \log n)$ via the FFT). It excels at capturing the global, smooth heat-transfer dynamics of the adsorption column. 
**The FNO Limitation:** Because the Fourier basis is composed of global sine and cosine waves, FNOs are notoriously susceptible to the Gibbs phenomenon (ringing artifacts) when attempting to resolve sharp discontinuities. In MOF adsorption, the mass-transfer zone (MTZ) propagates as a highly localized, sharp "shock front."

### 2.3 Localized Operators: Wavelet Neural Operator (WNO) & DeepONet
To counter the FNO's smoothing of sharp breakthrough shocks, recent literature has proposed the Wavelet Neural Operator (WNO), which utilizes localized multi-scale wavelets rather than global Fourier modes. We include WNO and standard Deep Operator Networks (DeepONet) as advanced state-of-the-art baselines. While they successfully localize the shock front, they remain purely data-driven operators that drift from true mass conservation over long cyclic integrations.

### 2.4 Our Contribution: PI-DeepOKAN and PIKAN
To solve the dual challenge of (1) enforcing thermodynamic physics and (2) resolving sharp local shock fronts without Fourier ringing, we introduce the **Physics-Informed Deep Operator KAN (PI-DeepOKAN)** and the foundational **PIKAN**.
**Why PIKAN/DeepOKAN?** 
1. **Localized RBF Bases:** Instead of standard MLP activation functions or global Fourier modes, our KAN layers employ highly localized Gaussian Radial Basis Functions (RBFs) on every network edge. This acts mathematically similarly to a wavelet, allowing the network to sharply resolve the breakthrough shock front without global oscillation.
2. **Infinite Differentiability:** Because RBFs are $C^\infty$ smooth, we can seamlessly backpropagate the second-order partial derivatives (for diffusion and heat conduction) through the network, allowing us to compute exact PDE residuals.
3. **White-Box Explainability:** Unlike MLPs or FNOs, which obscure physical meaning inside hidden matrices, the localized KAN edges can be extracted. When coupled with the Sparse Identification of Nonlinear Dynamics (SINDy), this allows us to symbolically extract the exact, non-linear kinetic rate equations governing flexible "breathing" MOFs directly from the network structure.

In summary, we benchmark our novel PI-DeepOKAN against Data-Driven MLPs, standard PINNs, FNOs, and WNOs to definitively prove that localized, physics-informed operator networks are the optimal mathematical architecture for simulating nanoporous multiphysics.
