from setuptools import setup

setup(
    name='nucapt-publish',
    version='0.0.1',
    packages=['nucapt'],
    description='Web service for keeping track of NUCAPT datasets',
    instal_requires=[
        'flask==0.12.2',
        'wtforms==2.1',
    ],
)
