from setuptools import setup, find_packages

setup(
    name="nexus_sdk",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["pysui==0.52.0", "setuptools"],
    description="Talus Nexus SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
    ],
)
