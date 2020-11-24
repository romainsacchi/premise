from setuptools import setup
import os

packages = []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

# Probably should be changed, __init__.py is no longer required for Python 3
for dirpath, dirnames, filenames in os.walk('rmnd_lca'):
    # Ignore dirnames that start with '.'
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='rmnd-lca',
    version="0.1.6",
    packages=packages,
    author="Alois Dirnaichner <dirnaichner@pik-potsdam.de>, Chris Mutel <chris.mutel@psi.ch>, Tom Terlouw <tom.terlouw@psi.ch>, Romain Sacchi <romain.sacchi@psi.ch>",
    # author_email="cmutel@gmail.com",
    license=open('LICENSE').read(),
    # Only if you have non-python data (CSV, etc.). Might need to change the directory name as well.
    include_package_data=True,
    install_requires=[
        'numpy',
        'wurst>=0.2',
        'bw2io',
        'pandas',
        'bw2data',
        'brightway2',
        'xarray>0.15.0',
        'carculator>=1.2.8',
        'prettytable',
        'pycountry'
    ],
    url="https://github.com/romainsacchi/rmnd-lca",
    description='Coupling REMIND output to ecoinvent LCA database ecoinvent for prospective LCA',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)
