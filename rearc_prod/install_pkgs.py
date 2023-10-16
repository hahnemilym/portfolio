##------------------------------------------##
##-- install_pkgs.py
##------------------------------------------##
import pkg_resources
from subprocess import call

def get_missing_packages(requirements_file):
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f]
    installed = {pkg.key for pkg in pkg_resources.working_set}
    return [pkg for pkg in requirements if pkg not in installed]

def install_missing_packages(missing):
    try:
        print(f"\nInstalling: {', '.join(missing)}")
        call(f"pip install {' '.join(missing)}", shell=True)
        #if missing!='node':
            #call(f"pip install {' '.join(missing)}", shell=True)
        #else:
            #call(f"brew install {' '.join(missing)}", shell=True)
    except:
        print(f"\nFailed: {', '.join(missing)}")

def verify_requirements(requirements_file):
    missing = get_missing_packages(requirements_file)
    if missing:
        install_missing_packages(missing)

if __name__ == '__main__':
    verify_requirements('requirements.txt')
    verify_requirements('requirements-aws.txt')