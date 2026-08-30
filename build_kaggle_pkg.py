"""Packages the AI MOF/COF Dynamics repository for Kaggle execution."""
import os
import zipfile

def package_for_kaggle():
    output_filename = "kaggle_mof_dynamics_pkg.zip"
    
    # Files to include
    files_to_zip = [
        "00_MASTER_PLAN_DYNAMICS.md",
        "solver_fd.py",
        "pde_adsorption.py",
        "kan_model.py",
        "operator_models.py",
        "baseline_models.py",
        "fno_model_adsorption.py",
        "train_pikan.py",
        "sindy_discovery.py",
        "plot_results.py",
        "data/synthetic_breakthrough.npz",
    ]
    
    print(f"Packaging {len(files_to_zip)} files into {output_filename}...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            if os.path.exists(file):
                zipf.write(file)
                print(f"  Added: {file}")
            else:
                print(f"  WARNING: Could not find {file}")
                
    print(f"Packaging complete. Upload {output_filename} to Kaggle.")

if __name__ == "__main__":
    package_for_kaggle()
