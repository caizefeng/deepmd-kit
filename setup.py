import importlib
import os
from distutils.util import get_platform
from os import path, makedirs

import pkg_resources
from packaging.version import LegacyVersion
from skbuild import setup
from skbuild.cmaker import get_cmake_version
from skbuild.exceptions import SKBuildError

readme_file = path.join(path.dirname(path.abspath(__file__)), 'README.md')
try:
    from m2r import parse_from_file

    readme = parse_from_file(readme_file)  # convert partial rst to md
except ImportError:
    with open(readme_file) as f:
        readme = f.read()

install_requires = ['numpy>=1.19', 'scipy>=1.5', 'pyyaml', 'dargs']
setup_requires = ['setuptools_scm', 'scikit-build']  # this legacy usage won't function cuz `skbuild` is imported before

tf_version = os.environ.get('TENSORFLOW_VERSION', '2.3')
if LegacyVersion(tf_version) < LegacyVersion("1.15") or (
        LegacyVersion("2.0") <= LegacyVersion(tf_version) < LegacyVersion("2.1")):
    extras_require = {"cpu": ["tensorflow==" + tf_version], "gpu": ["tensorflow-gpu==" + tf_version]}
else:
    extras_require = {"cpu": ["tensorflow-cpu==" + tf_version], "gpu": ["tensorflow==" + tf_version]}
tf_spec = importlib.util.find_spec("tensorflow")
if tf_spec:
    tf_install_dir = tf_spec.submodule_search_locations[0]
else:
    site_packages_path = path.join(path.dirname(path.__file__), 'site-packages')  # dunno what it is for
    tf_spec = importlib.machinery.FileFinder(site_packages_path).find_spec("tensorflow")
    if tf_spec:
        tf_install_dir = tf_spec.submodule_search_locations[0]
    else:
        setup_requires.append("tensorflow==" + tf_version)
        tf_install_dir = path.join(path.dirname(path.abspath(__file__)), '.egg',  # when installed by `setup_requires`
                                   pkg_resources.Distribution(project_name="tensorflow", version=tf_version,
                                                              platform=get_platform()).egg_name(),
                                   'tensorflow')

# add cmake as a build requirement if cmake>3.7 is not installed
try:
    if LegacyVersion(get_cmake_version()) < LegacyVersion("3.7"):
        setup_requires.append('cmake')
except SKBuildError:
    setup_requires.append('cmake')

try:
    makedirs('deepmd')
except OSError:
    pass

setup(
    name="deepmd-kit",
    setup_requires=setup_requires,
    use_scm_version={'write_to': 'deepmd/_version.py'},
    author="Han Wang",
    author_email="wang_han@iapcm.ac.cn",
    description="A deep learning package for many-body potential energy representation and molecular dynamics",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/deepmodeling/deepmd-kit",
    packages=['deepmd'],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
    keywords='deepmd',
    install_requires=install_requires,
    cmake_args=['-DTENSORFLOW_ROOT:STRING=%s' % tf_install_dir,
                '-DBUILD_PY_IF:BOOL=TRUE',
                '-DBUILD_CPP_IF:BOOL=TRUE',  # `pip install .` to install
                '-DFLOAT_PREC:STRING=high',
                ],
    cmake_source_dir='deepmd',
    cmake_minimum_required_version='3.0',
    extras_require={
        'test': ['dpdata>=0.1.9'],
        'docs': ['sphinx', 'recommonmark', 'sphinx_rtd_theme'],
        **extras_require,  # ease the dependency setting for upstream applications
    },
    entry_points={
        'console_scripts': ['dp = deepmd.train.main:main']
    }
)