from vllm import LLM, SamplingParams
from vllm.assets.image import ImageAsset

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Mistral Small 3.2 with vLLM")
    # print("Testing rednote-hilab/dots.ocr with vLLM")
    # print("Testing Gemma 4 with vLLM")
    print("=" * 50)

    # Initialize the model
    print("\nLoading model with vLLM...")
    llm = LLM(
        model="mistralai/Mistral-Small-3.2-24B-Instruct-2506",
        # model="rednote-hilab/dots.ocr",
        # model="google/gemma-4-26B-A4B-it",
        trust_remote_code=True,
        dtype="bfloat16",
        gpu_memory_utilization=0.7,
        max_model_len=32768,
        limit_mm_per_prompt={"image": 1},
        allowed_local_media_path="/home/sparrow/sparrow-data/parse/sparrow_parse/images/"
    )

    print("Model loaded successfully!")

    # Load your local image
    image_path = "/home/sparrow/sparrow-data/parse/sparrow_parse/images//bonds_table.png"

    # Create the prompt with image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                # {"type": "text", "text": "retrieve all data. return response in JSON format"}
                {"type": "text", "text": "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"}
            ]
        }
    ]

    # Generate
    print("\nProcessing image and generating response...")
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=4000
    )

    outputs = llm.chat(messages, sampling_params=sampling_params)

    print("\n" + "=" * 50)
    print("RESULT:")
    print("=" * 50)
    print(outputs[0].outputs[0].text)

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)
