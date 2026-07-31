import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, setup

extensions = [
    Extension(
        "cis_decoder",
        ["cis_decoder.pyx"],
        extra_compile_args=["-O2"],
    ),
]

setup(
    package_dir={"cis_decoder": ""},
    ext_modules=cythonize(extensions),
    include_dirs=[np.get_include()],
)
