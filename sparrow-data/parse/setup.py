from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sparrow-parse",
    version="1.5.9",
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
                "transformers==5.14.0",
                "torch==2.13.0",
                "torchvision==0.28.0",
                "numpy==2.5.2",
                "mistralai==2.9.3",
                "mlx==0.32.2; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.6.16; sys_platform == 'darwin' and platform_machine == 'arm64'",
            ],
            "linux": [
                "transformers==5.9.0",
                "torch==2.11.0",
                "torchvision==0.26.0",
                "numpy",
                "vllm==0.23.0; sys_platform == 'linux'",
            ],
            "all": [
                "transformers==5.14.0",
                "torch==2.13.0",
                "torchvision==0.28.0",
                "numpy==2.5.2",
                "mistralai==2.9.3",
                "mlx==0.32.2; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.6.16; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "vllm==0.23.0; sys_platform == 'linux'",
            ],
        },
    entry_points={
        'console_scripts': [
            'sparrow-parse=sparrow_parse:main',
        ],
    },
    keywords="llm, vllm, ocr, vision",
    packages=find_packages(),
    python_requires='>=3.12',
    install_requires=requirements,
)
