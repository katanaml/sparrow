import gradio as gr
import spaces
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
from datetime import datetime
import os

# subprocess.run('pip install flash-attn --no-build-isolation', env={'FLASH_ATTENTION_SKIP_CUDA_BUILD': "TRUE"}, shell=True)

DESCRIPTION = "[Sparrow Qwen2-VL-7B Backend](https://github.com/katanaml/sparrow)"


def array_to_image_path(image_filepath, max_width=1250, max_height=1750):
    if image_filepath is None:
        raise ValueError("No image provided. Please upload an image before submitting.")

    # Open the uploaded image using its filepath
    img = Image.open(image_filepath)

    # Extract the file extension from the uploaded file
    input_image_extension = image_filepath.split('.')[-1].lower()  # Extract extension from filepath

    # Set file extension based on the original file, otherwise default to PNG
    if input_image_extension in ['jpg', 'jpeg', 'png']:
        file_extension = input_image_extension
    else:
        file_extension = 'png'  # Default to PNG if extension is unavailable or invalid

    # Get the current dimensions of the image
    width, height = img.size

    # Initialize new dimensions to current size
    new_width, new_height = width, height

    # Check if the image exceeds the maximum dimensions
    if width > max_width or height > max_height:
        # Calculate the new size, maintaining the aspect ratio
        aspect_ratio = width / height

        if width > max_width:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)

        if new_height > max_height:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)

    # Generate a unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"image_{timestamp}.{file_extension}"

    # Save the image
    img.save(filename)

    # Get the full path of the saved image
    full_path = os.path.abspath(filename)

    return full_path, new_width, new_height


# Initialize the model and processor globally to optimize performance
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)

processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")


@spaces.GPU
def run_inference(input_imgs, text_input):
    results = []

    for image in input_imgs:
        # Convert each image to the required format
        image_path, width, height = array_to_image_path(image)

        try:
            # Prepare messages for each image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image_path,
                            "resized_height": height,
                            "resized_width": width
                        },
                        {
                            "type": "text",
                            "text": text_input
                        }
                    ]
                }
            ]

            # Prepare inputs for the model
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to("cuda")

            # Generate inference output
            generated_ids = model.generate(**inputs, max_new_tokens=4096)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            raw_output = processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=True
            )

            results.append(raw_output[0])

        finally:
            # Clean up the temporary image file
            os.remove(image_path)

    return results


css = """
  #output {
    height: 500px; 
    overflow: auto; 
    border: 1px solid #ccc; 
  }
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown(DESCRIPTION)
    with gr.Tab(label="Qwen2-VL-7B Input"):
        with gr.Row():
            with gr.Column():
                input_imgs = gr.Files(file_types=["image"], label="Upload Document Images")
                text_input = gr.Textbox(label="Query")
                submit_btn = gr.Button(value="Submit", variant="primary")
            with gr.Column():
                output_text = gr.Textbox(label="Response")

        submit_btn.click(run_inference, [input_imgs, text_input], [output_text])

demo.queue(api_open=True)
demo.launch(debug=True)