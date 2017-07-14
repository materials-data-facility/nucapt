from setuptools import setup

setup(
    name='nucapt-publish',
    version='0.0.1',
    packages=['nucapt'],
    description='Web service for keeping track of NUCAPT datasets',
    install_requires=[
        'flask==0.12.2',
        'wtforms==2.1',
        'pyyaml==3.12',
        'six==1.10.0',
        'jsonschema==2.6.0',
    ],
)
