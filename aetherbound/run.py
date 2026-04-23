import sys
import subprocess
import os
import time

def install_requirements():
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found.")
        sys.exit(1)
        
    # List of critical imports to check
    dependencies = [
        ("glfw", "glfw"),
        ("OpenGL", "PyOpenGL"),
        ("imgui", "imgui[glfw]"),
        ("pygame", "pygame"),
        ("numpy", "numpy"),
        ("glm", "PyGLM")
    ]
    
    missing = []
    for mod, pkg in dependencies:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
            
    if not missing:
        return

    print(f"Missing dependencies: {', '.join(missing)}")
    
    # Redundant pip commands to try
    pip_variants = [
        [sys.executable, "-m", "pip", "install"],
        ["pip", "install"]
    ]
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"\n--- Retry Attempt {attempt}/{max_retries} ---")
        
        # Strategy 1: Try requirements.txt with all pip variants
        for pip_cmd in pip_variants:
            try:
                print(f"Executing: {' '.join(pip_cmd)} -r {req_file}")
                subprocess.check_call(pip_cmd + ["-r", req_file])
                print("Dependencies installed successfully.")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
                
        # Strategy 2: Individual package installation with specific fallbacks
        print("Bulk installation failed. Attempting individual package recovery...")
        all_recovered = True
        for pkg in missing:
            pkg_recovered = False
            # Handle specific problematic packages like imgui[glfw]
            candidates = [pkg]
            if "imgui" in pkg:
                candidates.append("imgui") # Fallback to base imgui
                
            for cand in candidates:
                for pip_cmd in pip_variants:
                    try:
                        print(f"Attempting: {' '.join(pip_cmd)} {cand}")
                        subprocess.check_call(pip_cmd + [cand])
                        pkg_recovered = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                if pkg_recovered:
                    break
            
            if not pkg_recovered:
                all_recovered = False
                print(f"Failed to recover: {pkg}")
        
        if all_recovered:
            print("Successfully recovered all missing dependencies.")
            return
            
        if attempt < max_retries:
            print("Waiting before next attempt...")
            time.sleep(2)

    print("\nCRITICAL ERROR: Could not install required dependencies.")
    print("Please try manual installation: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    install_requirements()
    try:
        import main
        main.main()
    except Exception as e:
        print(f"\nAn error occurred while starting the game: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
