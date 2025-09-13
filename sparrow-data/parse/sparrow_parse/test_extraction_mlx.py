from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
import time


# Load model and processor
# model_path = "lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-MLX-8bit"
model_path = "mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit"
# model_path = "mlx-community/Qwen2.5-VL-72B-Instruct-3bit"
# model_path = "mlx-community/olmOCR-7B-0725-8bit" # fast and good
# model_path = "mlx-community/gemma-3-27b-it-qat-8bit"
vl_model, vl_processor = load(model_path)
vl_config = load_config(model_path)
print(f"Model loaded: {model_path}")

image = ["images/bonds_table.png"]

# Qwen
# prompt = [
#     {"role": "system", "content": "You are an expert at extracting text from images. Format your response in JSON."},
#     {"role": "user", "content": "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"}
# ]
# Qwen with bbox
# messages = [
#     {"role": "system", "content": "You are an expert at extracting text from images. For each item in the table, provide separate bounding boxes for each field. All coordinates should be in pixels relative to the original image. Format your response in JSON."},
#     {"role": "user", "content": "retrieve [{\"instrument_name\":{\"value\":\"str\", \"bbox\":[\"float\", \"float\", \"float\", \"float\"], \"confidence\":\"float\"}, \"valuation\":{\"value\":\"int\", \"bbox\":[\"float\", \"float\", \"float\", \"float\"], \"confidence\":\"float\"}}]. return response in JSON format"}
# ]
# Qwen with bbox, get all data
# messages = [
#     {"role": "system", "content": "You are an expert at extracting text from images. For each item in the table, provide separate bounding boxes for each field. All coordinates should be in pixels relative to the original image. Format your response in JSON."},
#     {"role": "user", "content": "retrieve all data. return response in JSON format. For each identified field or data element, include: 1) a descriptive field name as the object key, 2) a nested object with 'value' containing the extracted content, 'bbox' array with [x_min, y_min, x_max, y_max] coordinates in pixels, and 'confidence' score between 0-1. Example structure: [{\"field_name\":{\"value\":\"extracted value\", \"bbox\":[100, 200, 300, 250], \"confidence\":0.95}}]"}
# ]

# message = "retrieve all data. return response in JSON format"
prompt = "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"

formatted_prompt = apply_chat_template(vl_processor, vl_config, prompt, num_images=len(image))

script_start_time = time.time()

vl_output = generate(
    vl_model,
    vl_processor,
    formatted_prompt,
    image,
    max_tokens=4000,
    temperature=0,
    verbose=False
)

print(vl_output.text)

script_end_time = time.time()
total_execution_time = script_end_time - script_start_time

print(f"\nExecution time: {total_execution_time:.2f} seconds")


# Comment out below code if non Qwen model is used

# # Convert to a format we can draw on
# img_draw = image.copy()
# draw = ImageDraw.Draw(img_draw)
#
# # Parse the JSON result
# results = json.loads(vl_output.strip('```json\n').strip('```'))
#
# # Predefined solid colors that are highly visible
# solid_colors = [
#     (180, 30, 40),  # Dark red
#     (0, 100, 140),  # Dark blue
#     (30, 120, 40),  # Dark green
#     (140, 60, 160),  # Purple
#     (200, 100, 0),  # Orange
#     (100, 80, 0),  # Brown
#     (0, 100, 100),  # Teal
#     (120, 40, 100)  # Magenta
# ]
#
# # Determine unique field keys across all items to assign consistent colors
# unique_fields = set()
# for item in results:
#     unique_fields.update(item.keys())
#
# # Map each unique field to a color
# field_color_map = {}
# for i, field in enumerate(sorted(unique_fields)):
#     field_color_map[field] = solid_colors[i % len(solid_colors)]
#
# # Load font with larger size
# font_size = 20
# try:
#     font = ImageFont.truetype("arial.ttf", font_size)
# except IOError:
#     try:
#         font = ImageFont.truetype("DejaVuSans.ttf", font_size)
#     except IOError:
#         try:
#             font = ImageFont.truetype("Helvetica.ttf", font_size)
#         except IOError:
#             font = ImageFont.load_default()
#
#
# # Helper function to measure text width
# def get_text_dimensions(text, font):
#     try:
#         # Method for newer Pillow versions
#         left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
#         return right - left, bottom - top
#     except AttributeError:
#         try:
#             # Alternative method
#             left, top, right, bottom = font.getbbox(text)
#             return right - left, bottom - top
#         except AttributeError:
#             # Fallback approximation
#             return len(text) * (font_size // 2), font_size + 2
#
#
# # Draw bounding boxes for each item
# for item in results:
#     # Process each field
#     for field_name, field_data in item.items():
#         # Check if this field has the expected structure
#         if isinstance(field_data, dict) and "bbox" in field_data and "value" in field_data:
#             bbox = field_data["bbox"]
#             value = field_data["value"]
#             confidence = field_data.get("confidence", "N/A")
#
#             # Check if coordinates need to be scaled (normalized 0-1 values)
#             if all(isinstance(coord, (int, float)) for coord in bbox):
#                 if max(bbox) <= 1.0:  # Normalized coordinates
#                     width, height = image.size
#                     bbox = [
#                         bbox[0] * width,
#                         bbox[1] * height,
#                         bbox[2] * width,
#                         bbox[3] * height
#                     ]
#
#             # Get color from the mapping we created
#             color = field_color_map[field_name]
#
#             # Make sure bbox coordinates are integers
#             bbox = [int(coord) for coord in bbox]
#
#             # Calculate the bbox width
#             bbox_width = bbox[2] - bbox[0]
#
#             # Draw rectangle with appropriate thickness
#             border_thickness = 3
#             draw.rectangle(
#                 [(bbox[0], bbox[1]), (bbox[2], bbox[3])],
#                 outline=color,
#                 width=border_thickness
#             )
#
#             # Format the value and confidence
#             value_str = str(value)
#             confidence_str = f" [{confidence:.2f}]" if isinstance(confidence, (int, float)) else ""
#             prefix = f"{field_name}: "
#
#             # First, try with full text without truncation
#             full_label = prefix + value_str + confidence_str
#             full_width, text_height = get_text_dimensions(full_label, font)
#
#             # Compare with a reasonable maximum display width
#             min_display_width = 300  # Reasonable minimum width to display text
#             max_display_width = max(bbox_width * 1.5, min_display_width)
#
#             # Only truncate if the full text exceeds our maximum display width
#             if full_width > max_display_width:
#                 # Calculate the space available for the value
#                 prefix_width, _ = get_text_dimensions(prefix, font)
#                 confidence_width, _ = get_text_dimensions(confidence_str, font)
#                 available_value_width = max_display_width - prefix_width - confidence_width
#
#                 # Truncate the value to fit
#                 truncated_value = value_str
#                 for i in range(len(value_str) - 1, 3, -1):
#                     truncated_value = value_str[:i] + "..."
#                     temp_width, _ = get_text_dimensions(truncated_value, font)
#                     if temp_width <= available_value_width:
#                         break
#
#                 label = prefix + truncated_value + confidence_str
#                 text_width, _ = get_text_dimensions(label, font)
#             else:
#                 # No truncation needed
#                 label = full_label
#                 text_width = full_width
#
#             # Position for text (above the bounding box)
#             padding = 6
#             text_position = (bbox[0], bbox[1] - text_height - (padding * 2))
#
#             # Ensure text doesn't go off the top of the image
#             if text_position[1] < padding:
#                 # If too close to top, position below the box instead
#                 text_position = (bbox[0], bbox[3] + padding)
#
#             # Add a background rectangle with better contrast
#             draw.rectangle(
#                 [(text_position[0] - padding, text_position[1] - padding),
#                  (text_position[0] + text_width + padding, text_position[1] + text_height + padding)],
#                 fill=(255, 255, 255, 240),
#                 outline=color,
#                 width=2
#             )
#
#             # Draw the text
#             draw.text(
#                 text_position,
#                 label,
#                 fill=color,
#                 font=font
#             )
#
# # Save the annotated image
# output_path = "images/bonds_table_annotated.png"
# img_draw.save(output_path)
# print(f"Annotated image saved to {output_path}")