from mlx_vlm import load, apply_chat_template, generate
from mlx_vlm.utils import load_image

# Load model and processor
qwen_vl_model, qwen_vl_processor = load("mlx-community/Qwen2-VL-7B-Instruct-8bit")
qwen_vl_config = qwen_vl_model.config

image = load_image("images/graph.png")

messages = [
    {"role": "system", "content": "You are an expert at extracting text from images. Format your response in json."},
    {"role": "user", "content": "Extract the names, labels and y coordinates from the image."}
]

# Apply chat template
prompt = apply_chat_template(qwen_vl_processor, qwen_vl_config, messages)

# Generate text
qwen_vl_output = generate(
    qwen_vl_model,
    qwen_vl_processor,
    prompt,
    image,
    max_tokens=1000,
    temperature=0.7,
)

print(qwen_vl_output)