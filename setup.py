import setuptools


with open("README.md") as f:
    long_description = f.read()

with open("./src/vizneuron/__init__.py") as f:
    for line in f.readlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            version = line.split(delim)[1]
            break
    else:
        print("Can't find version! Stop Here!")
        exit(1)

setuptools.setup(
    name="vizneuron",
    version=version,
    author="Alexander Jipa",
    author_email="alexander.jipa@gmail.com",
    description="AWS Neuron plugins for VizTracer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clumsy/vizneuron",
    packages=setuptools.find_packages("src"),
    package_dir={"":"src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        "viztracer",
    ],
    extras_require={
        "lightning": ["pytorch-lightning"],
    },
    python_requires=">=3.8",
)
