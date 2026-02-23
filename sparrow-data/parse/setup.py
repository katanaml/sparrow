from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sparrow-parse",
    version="1.3.6",
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
                "transformers==5.1.0",
                "torch==2.10.0",
                "torchvision==0.25.0",
                "numpy==2.4.2",
                "mlx==0.30.6; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.3.12; sys_platform == 'darwin' and platform_machine == 'arm64'",
            ],
            "linux": [
                "transformers>=4.56.0,<5.0.0",
                "torch==2.9.1",
                "torchvision==0.24.1",
                "numpy>=1.24,<2.3",
                "vllm==0.15.1; sys_platform == 'linux'",
            ],
            "all": [
                "transformers==5.1.0",
                "torch==2.10.0",
                "torchvision==0.25.0",
                "numpy==2.4.2",
                "mlx==0.30.6; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "mlx-vlm==0.3.12; sys_platform == 'darwin' and platform_machine == 'arm64'",
                "vllm==0.15.1; sys_platform == 'linux'",
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
