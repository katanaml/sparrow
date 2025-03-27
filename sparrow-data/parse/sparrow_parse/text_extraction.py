from mlx_vlm import load, apply_chat_template, generate
from mlx_vlm.utils import load_image


# Load model and processor
# vl_model, vl_processor = load("mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit")
vl_model, vl_processor = load("mlx-community/Qwen2.5-VL-7B-Instruct-8bit")
vl_config = vl_model.config

image = load_image("images/bonds_table.png")

messages = [
    {"role": "system", "content": "You are an expert at extracting text from images. Format your response in json."},
    {"role": "user", "content": "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"}
]

# message = "retrieve all data. return response in JSON format"
# message = "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"

# Apply chat template
prompt = apply_chat_template(vl_processor, vl_config, messages)
# prompt = apply_chat_template(vl_processor, vl_config, message)

# Generate text
vl_output = generate(
    vl_model,
    vl_processor,
    prompt,
    image,
    max_tokens=1000,
    temperature=0,
    verbose=False
)

print(vl_output)