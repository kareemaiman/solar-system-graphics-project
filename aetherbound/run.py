import sys # For executable path and exit codes
import subprocess # To run PIP as a separate process
import os # Filesystem checks
import time # For retry delays

def install_requirements():
    """Ensures all third-party libraries are installed before the engine starts.
    
    Logic:
        1. Checks for module imports (glfw, imgui, etc.).
        2. If missing, attempts 'pip install -r requirements.txt'.
        3. On failure, attempts individual package recovery with fallback logic
           (e.g., trying 'imgui' if 'imgui[glfw]' fails).
        4. Retries up to 2 times before giving up.

    Args:

    Returns:

    """
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
    """
    Bootstrapper Entry Point.
    
    Sequence:
        1. Verify Dependencies.
        2. Import 'main' (deferred to after installation).
        3. Launch game loop.
        4. Catch and log fatal initialization errors.
    """
    install_requirements()
    try:
        # Deferred import ensures 'main' is loaded ONLY after pip finishes
        import main
        main.main()
    except Exception as e:
        print(f"\nAn error occurred while starting the game: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
