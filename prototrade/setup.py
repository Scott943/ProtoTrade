from setuptools import setup, find_packages

VERSION = '0.0.20'
DESCRIPTION = 'Parallelised Python framework for rapid prototyping of autotrading strategies'
setup(
    name='prototrade',
    version = VERSION,
    description= DESCRIPTION,
    author = 'Scott Parker',
    python_requires='>=3.8',
    packages=find_packages(
        where='src',
    ),
    package_dir={"": "src"},
    license="MIT",
    install_requires=[
    'matplotlib>=3.6.1',
    'numpy>=1.23.0',
    'alpaca_trade_api==2.3',
    'dash>=2.5.1, <3.0',
    'plotly>=5.9.0, <6.0',
    ]
    
)