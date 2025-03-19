from mlx_vlm import load, apply_chat_template, generate
from mlx_vlm.utils import load_image

# For test purposes, we will use a sample image

# Load model and processor
vl_model, vl_processor = load("mlx-community/Qwen2.5-VL-7B-Instruct-8bit")
vl_config = vl_model.config

image = load_image("images/graph.png")

messages = [
    {"role": "system", "content": "You are an expert at extracting text from images. Format your response in json."},
    {"role": "user", "content": "Extract the names, labels and coordinates from the image."}
]

# Apply chat template
prompt = apply_chat_template(vl_processor, vl_config, messages)

# Generate text
vl_output = generate(
    vl_model,
    vl_processor,
    prompt,
    image,
    max_tokens=1000,
    temperature=0,
)

print(vl_output)