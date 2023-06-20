# Sparrow ChatGPT Plugin - Receipt Assistant

## Description

Manage receipts with Sparrow. You can read, store and review your receipts. This plugin works with ChatGPT to process OCR output from [Sparrow Data](https://github.com/katanaml/sparrow/tree/main/sparrow-data) service.

## Usage

To install the required packages for this plugin, run the following command:

```
pip install -r requirements.txt
```

To run the plugin, enter the following command:

```
python main.py
```

Once the local server is running:

1. Navigate to https://chat.openai.com.
2. In the Model drop down, select "Plugins" (note, if you don't see it there, you don't have access yet).
3. Select "Plugin store"
4. Select "Develop your own plugin"
5. Enter in localhost:5003 since this is the URL the server is running on locally, then select "Find manifest file".

The plugin should now be installed and enabled! You can start with a question like "What is on my todo list" and then try adding something to it as well!

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
