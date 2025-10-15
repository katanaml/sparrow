from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sparrow-parse",
    version="1.1.4",
    author="Andrej Baranovskij",
    author_email="andrejus.baranovskis@gmail.com",
    description="Sparrow Parse is a Python package (part of Sparrow) for parsing and extracting information from documents.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/katanaml/sparrow/tree/main/sparrow-data/parse",
    project_urls={
        "Homepage": "https://github.com/katanaml/sparrow/tree/main/sparrow-data/parse",
        "Repository": "https://github.com/katanaml/sparrow",
    },
    classifiers=[
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3.10",
    ],
        extras_require={
            "mlx": [
                "mlx==0.29.2; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.3.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
            ],
            "all": [
                "mlx==0.29.2; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.3.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
            ],
        },
    entry_points={
        'console_scripts': [
            'sparrow-parse=sparrow_parse:main',
        ],
    },
    keywords="llm, vllm, ocr, vision",
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=requirements,
)
