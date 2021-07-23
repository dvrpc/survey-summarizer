from setuptools import find_packages, setup

setup(
    name="src",
    packages=find_packages(),
    version="0.1.0",
    description="Summarize results from Google Form surveys using Python (+ pandas and xlsxwriter)",
    author="Aaron Fraint, AICP",
    license="GNU GPL v3",
    entry_points="""
        [console_scripts]
        survey=src.cli:main
    """,
)
