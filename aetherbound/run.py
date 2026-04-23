import sys
import subprocess
import os

def install_requirements():
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found.")
        sys.exit(1)
        
    try:
        import glfw
        import OpenGL
        import imgui
        import pygame
        import numpy
        import glm
    except ImportError:
        print("Missing dependencies. Installing from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("Dependencies installed successfully.")

if __name__ == "__main__":
    install_requirements()
    import main
    main.main()
