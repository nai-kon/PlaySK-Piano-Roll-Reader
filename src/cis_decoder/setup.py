import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    package_dir={"cis_decoder": ""},
    ext_modules=cythonize("cis_decoder.pyx"),
    include_dirs=[np.get_include()]
)
