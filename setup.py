from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
import glob
import os
import pkg_resources

from grinch import __version__, _program

setup(name='grinch',
      version=__version__,
      packages=find_packages(),
      scripts=["grinch/scripts/grinch_report.smk",
                "grinch/scripts/render_report.smk",
                "grinch/scripts/parallel_pangolin.smk",
                "grinch/scripts/data_for_website.py",
                "grinch/scripts/update_website.py"],
      package_data={"grinch":["data/*","data/flights/*"]},
      install_requires=[
            "biopython>=1.70",
            "pytools>=2020.1",
            'pandas>=1.0.1',
            'pysam>=0.15.4',
            "matplotlib>=3.2.1",
            "scipy>=1.4.1",
            "numpy>=1.13.3",
            "geopandas>=0.7.0",
            "descartes>=1.1.0",
            "adjustText>=0.7.3",
            "tabulate>=0.8.7",
            "seaborn>=0.10.1",
            "epiweeks>=2.1.2"
        ],

      description='new variant reporting tool',
      url='https://github.com/aineniamh/grinch',
      author='Aine OToole, Verity Hill',
      author_email='aine.otoole@ed.ac.uk',
      entry_points="""
      [console_scripts]
      {program} = grinch.command:main
      """.format(program = _program),
      include_package_data=True,
      keywords=[],
      zip_safe=False)
