from pathlib import Path
from pkg_resources import parse_requirements
from setuptools import setup, find_packages
from src.mouseapp import __version__

with Path('requirements.txt').open() as requirements_txt:
    requirements = [str(req) for req in parse_requirements(requirements_txt)]

setup(name='mouseapp',
      version=__version__,
      package_dir={"": "src"},
      packages=find_packages("src"),
      install_requires=requirements)
