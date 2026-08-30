"""Sparse Identification of Nonlinear Dynamics (SINDy) for MOF Kinetics.

Standard engineering assumes the Linear Driving Force (LDF) model:
    dq/dt = k * (q* - q)

Flexible MOFs (like MIL-53) exhibit "breathing" transitions, making their 
kinetics highly non-linear. This script uses Sequential Threshold Ridge Regression 
(STRidge) to discover the true underlying ODE from data.

It builds a library of candidate functions: [1, q, q^2, q^3, c, c^2, q*c, ...]
and sparsifies the weights to find the exact governing equation.
"""
import numpy as np
import torch

class SINDy_Discoverer:
    def __init__(self, threshold=0.1, alpha=1.0, max_iter=100):
        self.threshold = threshold
        self.alpha = alpha
        self.max_iter = max_iter
        
    def build_library(self, q, c, q_star):
        """Builds the feature library Theta(X).
        q: Solid uptake
        c: Gas concentration
        q_star: Equilibrium uptake
        """
        N = len(q)
        # Base features
        ones = np.ones((N, 1))
        
        # Polynomials and interactions
        Theta = np.hstack([
            ones,
            q, c, q_star,
            q**2, c**2, (q_star)**2,
            q * c, q * q_star, c * q_star,
            q**3, c**3
        ])
        
        self.feature_names = [
            "1", "q", "c", "q*", 
            "q^2", "c^2", "(q*)^2", 
            "q*c", "q*q*", "c*q*", 
            "q^3", "c^3"
        ]
        
        return Theta
        
    def STRidge(self, Theta, dQ_dt):
        """Sequential Threshold Ridge Regression."""
        # Initial Ridge Regression: W = (Theta^T Theta + alpha I)^-1 Theta^T dQ
        dim = Theta.shape[1]
        W = np.linalg.inv(Theta.T @ Theta + self.alpha * np.eye(dim)) @ Theta.T @ dQ_dt
        
        # Sequential thresholding
        for k in range(self.max_iter):
            small_inds = np.abs(W) < self.threshold
            W[small_inds] = 0
            
            big_inds = ~small_inds
            if np.sum(big_inds) == 0:
                break
                
            # Regress only on large weights
            Theta_big = Theta[:, big_inds.flatten()]
            W_big = np.linalg.inv(Theta_big.T @ Theta_big + self.alpha * np.eye(np.sum(big_inds))) @ Theta_big.T @ dQ_dt
            
            W[big_inds] = W_big.flatten()
            
        return W

    def discover(self, q, c, q_star, dQ_dt):
        print("--- SINDy Kinetic Discovery ---")
        Theta = self.build_library(q, c, q_star)
        W = self.STRidge(Theta, dQ_dt)
        
        # Print the discovered equation
        equation = "dq/dt = "
        terms = []
        for i, w in enumerate(W):
            if np.abs(w) > 0:
                terms.append(f"{w[0]:.4f} * {self.feature_names[i]}")
                
        if len(terms) == 0:
            equation += "0"
        else:
            equation += " + ".join(terms)
            
        print("Discovered Kinetic Law:")
        print(equation)
        return W

if __name__ == "__main__":
    # Test on real MOF-303 Data
    data = np.load("data/mof303_breakthrough.npz")
    y = data["y"]
    N_z = len(data["z"])
    
    # Extract c and q at a specific column node (e.g., middle of the bed)
    node_idx = N_z // 2
    c = y[node_idx, :].reshape(-1, 1)
    q = y[N_z + node_idx, :].reshape(-1, 1)
    T = y[2 * N_z + node_idx, :].reshape(-1, 1)
    
    # Calculate q_star based on MOF-303 physics
    b0 = 4.0 / np.exp(45000.0 / (8.314 * 298.0))
    b = b0 * np.exp(45000.0 / (8.314 * T))
    q_star = 25.0 * b * c / (1 + b * c)
    
    # Calculate dQ_dt (numerical derivative of the data)
    t = data["t"]
    dt = np.gradient(t).reshape(-1, 1)
    dQ_dt = np.gradient(q, axis=0) / dt
    
    discoverer = SINDy_Discoverer(threshold=0.005)
    discoverer.discover(q, c, q_star, dQ_dt)
