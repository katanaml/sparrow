# ChangeLog

## [v0.2.3] - 2024-12-16

## Table processing

Added support auto detect tables and send cropped table images for inference


## [v0.2.2] - 2024-11-24

## Multi-page PDF document support

Added support for multi-page PDF document through CMD and API

## [v0.2.1] - 2024-11-08

## Dependencies cleanup

Removed dependencies to LlamaIndex, Haystack, Unstructured and other libraries, as main Sparrow focus is on Sparrow Parse

## [v0.2.0] - 2024-09-04

## Sparrow Parse with Vision LLM support

This release starts new phase in Sparrow development - Vision LLM support for document data processing.

1. Sparrow Parse library supports Vision LLM
2. Sparrow Parse provides factory class implementation to run inference locally or on cloud GPU
3. Sparrow supports JSON as input query
4. JSON query validation and LLM response JSON validation is performed

## [v0.1.8] - 2024-07-02

### New Features

- Sparrow Parse integration

### What's Changed

- Sparrow Parse is integrated into Instructor agent. README updated with example for Instructor agent

  

## [v0.1.7] - 2024-04-23

### New Features

- New Instructor agent

### What's Changed

- Added instructor agent for better JSON response generation



## [v0.1.6] - 2024-04-17

### New Features

- New agents with Unstructured

### What's Changed

- Added unstructured-light and unstructured agents for better data pre-processing




## [v0.1.5] - 2024-03-27

### New Features

- Virtual Environments support

### What's Changed

- Fixes in LlamaIndex agent to run with latest LlamaIndex versions
- LLM function calling agent




## [v0.1.4] - 2024-03-07

### New Features

- OCR + LLM support, new vprocessor agent

### What's Changed

- Improved FastAPI endpoints




## [v0.1.3] - 2024-02-11

### New Features

- Added Haystack agent for structured data

### What's Changed

- Changed plugins to agents

  

## [v0.1.2] - 2024-01-31

### New Features

- Added support for plugin architecture. This allows to use within Sparrow various toolkits, such as LlamaIndex or Haystack

### What's Changed

- Significant code refactoring

  

## [v0.1.1] - 2024-01-19

### New Features

- Minor improvements related to data ingestion

### What's Changed

- Fixed bug to clean Vector DB, when new document is inserted
- Tested with Notus and Openhermes LLMs
- Tested with longer and more realistic documents
- Upgraded LlamaIndex and LangChain



## [v0.1.0] - 2024-01-12

### New Features

- Lemming LLM RAG

### What's Changed

- 
