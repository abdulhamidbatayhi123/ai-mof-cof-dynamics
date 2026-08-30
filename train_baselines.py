"""Trains standard data-driven ML models to prove extrapolation failure.

This script demonstrates that traditional data-driven models (Random Forest, 
XGBoost, SVR, MLP, etc.) can perfectly interpolate training data, but completely 
hallucinate and fail when predicting unseen temporal domains (extrapolation), 
which is the core argument for needing Physics-Informed models.
"""
import numpy as np
import time
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.kernel_ridge import KernelRidge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

def load_split_data():
    """Loads breakthrough data and splits into Train (t<300) and Extrapolate (t>=300)."""
    data = np.load("data/synthetic_breakthrough.npz")
    z = data["z"]
    t = data["t"]
    y = data["y"]
    
    N_z = len(z)
    N_t = len(t)
    
    Z, T_grid = np.meshgrid(z, t, indexing='ij')
    Z_flat = Z.flatten()
    T_flat = T_grid.flatten()
    
    C = y[0:N_z, :].flatten()
    Q = y[N_z:2*N_z, :].flatten()
    Temp = y[2*N_z:3*N_z, :].flatten()
    
    X = np.column_stack((Z_flat, T_flat))
    Y = np.column_stack((C, Q, Temp))
    
    # Split: Train on first half of time, Extrapolate on second half
    t_split = 300.0
    train_idx = X[:, 1] < t_split
    test_idx = X[:, 1] >= t_split
    
    X_train, Y_train = X[train_idx], Y[train_idx]
    X_test, Y_test = X[test_idx], Y[test_idx]
    
    # Subsample training data to simulate sparse experimental data (1000 points)
    np.random.seed(42)
    sample_idx = np.random.choice(len(X_train), min(1000, len(X_train)), replace=False)
    X_train = X_train[sample_idx]
    Y_train = Y_train[sample_idx]
    
    return X_train, Y_train, X_test, Y_test

def run_baselines():
    X_train, Y_train, X_test, Y_test = load_split_data()
    print(f"Data Loaded. Training points: {len(X_train)}, Extrapolation points: {len(X_test)}")
    
    models = {
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "AdaBoost": MultiOutputRegressor(AdaBoostRegressor(random_state=42)),
        "MLP (Black-box NN)": MLPRegressor(hidden_layer_sizes=(64, 64, 64), max_iter=1000, random_state=42),
        "SVR (RBF)": MultiOutputRegressor(SVR(C=1.0, epsilon=0.1)),
        "Kernel Ridge": MultiOutputRegressor(KernelRidge(kernel='rbf', gamma=0.1))
    }
    
    if HAS_XGB:
        models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
        
    print("\n--- Model Performance (MSE) on (c, q, T) ---")
    print(f"{'Model Name':<20} | {'Train MSE (Interpolation)':<25} | {'Test MSE (Extrapolation)':<25}")
    print("-" * 75)
    
    results = {}
    
    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, Y_train)
        
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        mse_train = mean_squared_error(Y_train, y_pred_train)
        mse_test = mean_squared_error(Y_test, y_pred_test)
        
        t_elapsed = time.time() - t0
        
        print(f"{name:<20} | {mse_train:<25.4e} | {mse_test:<25.4e} | ({t_elapsed:.1f}s)")
        
        results[name] = {"train_mse": mse_train, "test_mse": mse_test}
        
if __name__ == "__main__":
    run_baselines()
