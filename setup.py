from distutils.core import setup
from bake.packaging import *

setup(
    name='nucleus',
    version='0.0.1',
    packages=enumerate_packages('nucleus'),
    package_data={
        'nucleus.bindings': ['*.mesh'],
    }
)
