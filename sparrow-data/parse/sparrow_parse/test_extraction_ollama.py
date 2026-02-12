import ollama
import json
import os
import time
from typing import Dict, Any, List

def test_ollama_multimodal_extraction():
    """
    Test Ollama multimodal request with image input and structured data extraction.
    """

    # Configuration
    model_name = "mistral-small3.2:24b-instruct-2506-q8_0"
    image_path = "images/bonds_table.png"
    query = 'retrieve [{"instrument_name":"str", "valuation":"int"}]. return response in JSON format'

    try:
        # Check if image file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found.")
            return None

        print(f"Testing Ollama multimodal extraction...")
        print(f"Model: {model_name}")
        print(f"Image: {image_path}")
        print(f"Query: {query}")
        print("-" * 50)

        # Make the multimodal request to Ollama
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': query,
                    'images': [image_path]
                }
            ]
        )

        # Extract the response content
        response_content = response['message']['content']
        print("Raw response:")
        print(response_content)
        print("-" * 50)

        return response_content

    except Exception as e:
        print(f"Error during Ollama request: {e}")
        return None

def test_ollama_connection():
    """
    Test basic connection to Ollama and check if the model is available.
    """
    try:
        print("Testing Ollama connection...")

        # List available models
        models_response = ollama.list()

        # Extract model names from the ListResponse object
        model_names = [model.model for model in models_response.models]
        print(f"Available models: {model_names}")

        target_model = "mistral-small3.2:24b-instruct-2506-q8_0"
        if target_model in model_names:
            print(f"✓ Target model '{target_model}' is available")
            return True
        else:
            print(f"✗ Target model '{target_model}' is not available")
            print("You may need to pull the model first:")
            print(f"  ollama pull {target_model}")
            return False

    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Make sure Ollama is running (ollama serve)")
        return False

def main():
    """
    Main function to run the Ollama multimodal test.
    """

    print("Ollama Multimodal Extraction Test")
    print("=" * 50)

    # Test connection first
    if not test_ollama_connection():
        return

    print("\n" + "=" * 50)

    start_time = time.time()

    # Run the multimodal extraction test
    result = test_ollama_multimodal_extraction()

    if result:
        print("\n" + "=" * 50)
        print("Test completed successfully!")
    else:
        print("\n" + "=" * 50)
        print("Test failed or returned no results.")

    # Record end time and calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nExecution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()