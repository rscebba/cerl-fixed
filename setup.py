import pathlib
import setuptools

here = pathlib.Path(__file__).parent
readme = (here / 'README.md').read_text()

setuptools.setup(
    name=               "cerl",
    version=            "0.0.5",
    author=             "Andreas Walker",
    author_email=       "walker@sub.uni-goettingen.de",
    description=        "Library for querying CERL infrastructure",
    long_description=   readme,
    long_description_content_type="text/markdown",
    license=            "MIT",
    packages=           setuptools.find_packages(),
    classifiers=        [
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        "requests",
    ],
    python_requires=    '>=3.8.5'
)