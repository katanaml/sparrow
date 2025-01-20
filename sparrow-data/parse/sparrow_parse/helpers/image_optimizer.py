from PIL import Image
import os


class ImageOptimizer(object):
    def __init__(self):
        pass

    def crop_image_borders(self, file_path, temp_dir, debug_dir=None, crop_size=60):
        """
        Crops all four borders of an image by the specified size.

        Args:
            file_path (str): Path to the input image
            temp_dir (str): Temporary directory to store the cropped image
            debug_dir (str, optional): Directory to save a debug copy of the cropped image
            crop_size (int): Number of pixels to crop from each border

        Returns:
            str: Path to the cropped image in temp_dir
        """
        try:
            # Open the image
            with Image.open(file_path) as img:
                # Get image dimensions
                width, height = img.size

                # Calculate the crop box
                left = crop_size
                top = crop_size
                right = width - crop_size
                bottom = height - crop_size

                # Ensure we're not trying to crop more than the image size
                if right <= left or bottom <= top:
                    raise ValueError("Crop size is too large for the image dimensions")

                # Perform the crop
                cropped_img = img.crop((left, top, right, bottom))

                # Get original filename without path
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)

                # Save cropped image in temp_dir
                output_path = os.path.join(temp_dir, f"{name}_cropped{ext}")
                cropped_img.save(output_path)

                # If debug_dir is provided, save a debug copy
                if debug_dir:
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, f"{name}_cropped_debug{ext}")
                    cropped_img.save(debug_path)
                    print(f"Debug cropped image saved to: {debug_path}")

                return output_path

        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")