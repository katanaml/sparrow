# Sparrow Data OCR

## Description

This module implements OCR functionality for Sparrow.

## Install

*Setup Python Environment (Sparrow is tested with Python 3.10.4) with `pyenv`:*

1. Install `pyenv`:

If you haven't already installed `pyenv`, you can do so using Homebrew with the following command:

```
brew update
brew install pyenv

```

2. Install the desired Python version:

With `pyenv` installed, you can now install a specific version of Python. For example, to install Python 3.10.4, you would use:

```
pyenv install 3.10.4
```

You can check available Python versions by running `pyenv install --list`.

3. Set the global Python version:

Once the installation is complete, you can set the desired Python version as the default (global) version on your system:

```
pyenv global 3.10.4
```

This command sets Python 3.10.4 as the default version for all shells.

4. Verify the change:

To ensure the change was successful, you can verify the current Python version by running:

```
python --version
```

If the output doesn’t reflect the change, you may need to restart your terminal or add `pyenv` to your shell's initialization script as follows:

5. Configure your shell's initialization script:

Add `pyenv` to your shell by adding the following lines to your `~/.bash_profile`, `~/.zprofile`, `~/.bashrc`, or `~/.zshrc` file:

```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

After adding these lines, restart your terminal or source your profile script with `source ~/.bash_profile` (or the appropriate file for your shell).

*Create Virtual Environment*

Create virtual environment in `sparrow-data/ocr` folder:

```
python -m venv .env_ocr
```

*Activate Virtual Environment and Install Dependencies*

Activate each environment and install its dependencies using the corresponding `requirements.txt` file.

For `ocr` environment:

1. Activate the environment:

```
source .env_ocr/bin/activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

If you are on Linux, it might be required to install poppler:

```
!apt-get install poppler-utils libpoppler-cpp-dev
!pip install -v -v python-poppler
```

## Run Sparrow OCR app

You may need to change port in api.py

```
python api.py
```

## Sparrow OCR

If you want to test how OCR works, you can run this API request through CURL

```
curl -X 'POST' \
  'http://127.0.0.1:8001/api/v1/sparrow-ocr/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=' \
  -F 'image_url=https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/inout-20211211_001.jpg'
```

## Commercial usage

Sparrow is available for free commercial use. This offer applies to organizations with gross revenue below $5 million USD in the past 12 months.

For businesses exceeding this revenue limit and seeking to bypass GPL license restrictions, please contact me at abaranovskis@redsamuraiconsulting.com to discuss dual licensing options. The same applies if you are looking for custom workflows to automate business processes, consulting options, and support/maintenance options.

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the GPL 3.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
