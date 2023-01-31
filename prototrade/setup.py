from setuptools import setup, find_packages

VERSION = '0.0.7'
DESCRIPTION = 'Parallelised Python framework for rapid prototyping of autotrading strategies'
setup(
    name='prototrade',
    version = VERSION,
    author = 'Scott Parker',
    email = 'scott.parker.uk@btinternet.com',
    packages=find_packages(
        where='src',
    ),
    package_dir={"": "src"},
    license="MIT",
    install_requires=[
    'matplotlib',
    'numpy',
    'alpaca_trade_api',
    'pandas',
    ]
    
)