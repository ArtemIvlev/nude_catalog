from setuptools import setup, find_packages

setup(
    name="nude_catalog",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "Pillow",
        "torch",
        "tensorflow",
        "tqdm",
        "imagehash",
    ],
) 