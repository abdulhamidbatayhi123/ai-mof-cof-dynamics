> # ⚠ SUPERSEDED — historical plan, not a statement of results
>
> Superseded 2026-08-30. Retained as provenance: this is what the project set out
> to do, and the gap between it and what the evidence supports is itself part of
> the record.
>
> Of the six planned contributions, the ladder **eliminated or refuted five**:
> PIKAN as "the explainable solver" (L3), physics-as-a-loss as the extrapolation
> fix (L4/L4b — it helps on one axis and hurts on the other), neural operators as
> the scaling answer (L5), SINDy for breathing kinetics (**A7** — no breathing
> physics exists in the data), and separate identification (L6 — H1 NOT
> SUPPORTED). Neural Implicit Flow was never attempted.
>
> The position the evidence actually supports is in `CONTINUE_HERE.md` §1 and
> `RESULTS.md`. Do not plan from this file.

# MASTER PLAN — Foundation Digital Twin for MOF and COF Adsorption Dynamics

> **Philosophy: Quality over everything.** This project transitions the ML-MOF/COF field from data-driven equilibrium memorization to physics-informed spatiotemporal operator learning.

**Goal:** Build a comprehensive, multi-architecture "Digital Twin" pipeline that solves the stiff mass- and heat-transfer PDEs of water/gas adsorption in porous frameworks (MOFs and COFs) in real-time. By enforcing physical laws (Fickian diffusion, energy conservation, thermodynamic consistency), we eliminate the "data hallucination" problem inherent to standard AI and achieve extreme generalization.

## The Blueprint & Narrative Arc

### 1. The Physical Problem & The Barrier
We model the 1D Adsorption Column (Breakthrough Curves).
- **Physics:** Coupled stiff PDEs (Mass Conservation, Energy Conservation, Adsorption Kinetics).
- **The Barrier:** Traditional solvers (Finite Volume/Finite Element like COMSOL) take hours per simulation. Screening thousands of MOFs/COFs for device-level atmospheric water harvesting (AWH) is currently computationally prohibitive.

### 2. The Data Illusion (Data-Driven Baselines)
- Train standard MLPs, XGBoost, and data-driven KANs on limited breakthrough curve data.
- **Hypothesis:** They will interpolate well but fail catastrophically when extrapolating to unseen boundary conditions (new inlet pressures, temperatures) or unseen COFs because they lack physical grounding.

### 3. Physics-Informed Neural Networks (PINN): The Extrapolation Solution
- Formulate the PDE loss function (Mass, Heat, Kinetics).
- Implement a PINN (using lessons from the machining project to handle stiffness via reference-anchoring).
- **Result:** Perfect extrapolation to unseen cycles/conditions.
- **Limitation:** The PINN remains an opaque black box.

### 4. Physics-Informed KAN (PIKAN): The Explainable Solver
- Swap the PINN backbone for a localized-RBF KAN.
- **The Magic:** Extract the 1D KAN edge functions to reveal the exact, closed-form algebraic equations governing the system. We will symbolically extract the kinetic rate laws, directly addressing the explainability gap in AI for chemistry.

### 5. Scaling to the Digital Twin: Neural Operators (FNO & DeepONet)
- A PIKAN solves one specific scenario (e.g., constant inlet humidity). A true Digital Twin must handle arbitrary continuous input functions RH(t) (like a changing desert weather profile).
- Train a **Physics-Informed DeepONet / FNO** to map the weather profile to the spatiotemporal water yield field inside the MOF bed.
- **Result:** Real-time (millisecond) simulation of AWH devices across a continuous parameter space.

### 6. The Frontier: SINDy & Neural Implicit Flow (The "Special Sauce")
- **SINDy:** Flexible MOFs (e.g., MIL-53) have non-linear "breathing" kinetics that defy the standard Linear Driving Force (LDF) model. Apply SINDy to discover the hidden non-linear ODEs governing structural breathing during adsorption.
- **Neural Implicit Flow (NIF):** Compress the complex 3D Zeo++ pore geometry of COFs into a mathematical latent space, allowing the DeepONet to solve fluid dynamics across the exact 3D crystal topology rather than just a 1D column.

## Phase 1 Execution Plan (Current Focus)
1. **Mathematical Formulation:** Write the exact normalized 1D Adsorption PDEs in PyTorch.
2. **Synthetic Data Generator:** Build a robust, highly verified Finite Volume (FV) or Finite Difference (FD) solver to generate the ground-truth breakthrough curves (concentration and temperature over time and space). This is our "anchor" data.
3. **PIKAN/PINN Base Code:** Adapt `parametric_hybrid.py` and `kan_model.py` from the machining project to accept the new multiphysics loss function.

---
*Let's make our dreams real.*
