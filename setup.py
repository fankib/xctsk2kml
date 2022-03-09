import setuptools

setuptools.setup(
    name="xctsk2kml",
    version="0.1",
    author="Benjamin Fankhauser",
    author_email="nimajneb_fankhauser@hotmail.com",
    description=".xctsk to .kml (Google earth) converter",
    long_description='This tool allows to present task from XCTrack in google earth.',
    long_description_content_type="text/markdown",
    url="https://github.com/fankib/xctsk2kml",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "argparse",
        "pykml",
        "lxml"
    ],
    entry_points={
        "console_scripts": [
            "xctsk2kml = xctsk2kml.main:main"
        ],
    },
    python_requires='>=3.5',
)
