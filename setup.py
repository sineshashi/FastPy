from setuptools import setup, find_packages

setup(
    name="fastpy-rest",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.1.1"
    ]
)
