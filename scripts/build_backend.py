import os
import subprocess
import sys

def main():
    print("Building TOBU Backend with PyInstaller using tobu-server.spec...")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    spec_path = os.path.join(project_root, "tobu-server.spec")

    if not os.path.exists(spec_path):
        print(f"Error: {spec_path} not found!")
        sys.exit(1)

    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        spec_path
    ]

    print("Running command:", " ".join(args))
    env = os.environ.copy()
    # Ensure project root is in PYTHONPATH
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
    
    subprocess.check_call(args, cwd=project_root, env=env)
    print("Build complete!")

if __name__ == "__main__":
    main()

