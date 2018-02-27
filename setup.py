#!/usr/bin/env python

from setuptools import setup, find_packages


VERSION = '0.1.0ih1'

setup(
    name='dexbot',
    version=VERSION,
    description='Trading bot for the DEX (BitShares)',
    long_description=open('README.md').read(),
    author='Ian Haywood',
    author_email='ihaywood3@gmail.com',
    maintainer='Ian Haywood',
    maintainer_email='',
    url='http://www.github.com/ihaywood3/dexbot',
    keywords=['DEX', 'bot', 'trading', 'api', 'blockchain'],
    packages=[
        "dexbot",
        "dexbot.strategies",
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'dexbot = dexbot.cli:main',
        ],
    },
    install_requires=[
        "bitshares>=0.1.11",
        "uptick>=0.1.4",
        "prettytable",
        "click",
        "click-datetime",
        "colorama",
        "tqdm",
        "pyyaml",
        "sqlalchemy",
        "appdirs",
        #"pyqt5",
	"sdnotify",
        "ruamel.yaml",
        "matplotlib"
    ],
    dependency_links=[
        # Temporally force downloads from a different repo, change this once the websocket fix has been merged
        "https://github.com/mikakoi/python-bitshares/tarball/websocket-fix#egg=bitshares-0.1.11.beta"
    ],
    include_package_data=True,
)
