def process_ocr_data(file_path, input_data):
    """
    Callback method for ocr processing.
    This callback is invoked by the library when ocr processing is needed.

    Args:
        file_path: Path to the input file
        input_data: Input data to process

    Returns:
        input_data: The same input data unchanged
    """
    # For now, this method does nothing and just returns the input data
    print("Processing ocr data...")
    return input_data