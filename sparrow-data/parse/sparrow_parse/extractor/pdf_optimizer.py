import PyPDF2
from pdf2image import convert_from_path
import os
import tempfile
import shutil


class PDFOptimizer(object):
    def __init__(self):
        pass

    def split_pdf_to_pages(self, file_path, output_dir=None, convert_to_images=False):
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        output_files = []

        if not convert_to_images:
            # Open the PDF file
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                number_of_pages = len(reader.pages)

                # Split the PDF into separate files per page
                for page_num in range(number_of_pages):
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[page_num])

                    output_filename = os.path.join(temp_dir, f'page_{page_num + 1}.pdf')
                    with open(output_filename, 'wb') as output_file:
                        writer.write(output_file)
                        output_files.append(output_filename)

                    if output_dir:
                        # Save each page to the debug folder
                        debug_output_filename = os.path.join(output_dir, f'page_{page_num + 1}.pdf')
                        with open(debug_output_filename, 'wb') as output_file:
                            writer.write(output_file)

            # Return the number of pages, the list of file paths, and the temporary directory
            return number_of_pages, output_files, temp_dir
        else:
            # Convert the PDF to images
            images = convert_from_path(file_path, dpi=400)

            # Save the images to the temporary directory
            for i, image in enumerate(images):
                output_filename = os.path.join(temp_dir, f'page_{i + 1}.jpg')
                image.save(output_filename, 'JPEG')
                output_files.append(output_filename)

                if output_dir:
                    # Save each image to the debug folder
                    debug_output_filename = os.path.join(output_dir, f'page_{i + 1}.jpg')
                    image.save(debug_output_filename, 'JPEG')

            # Return the number of pages, the list of file paths, and the temporary directory
            return len(images), output_files, temp_dir


if __name__ == "__main__":
    pdf_optimizer = PDFOptimizer()

    # output_directory = "/Users/andrejb/Documents/work/bankstatement/output_pages"
    # # Ensure the output directory exists
    # os.makedirs(output_directory, exist_ok=True)
    #
    # # Split the optimized PDF into separate pages
    # num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages("/Users/andrejb/Documents/work/bankstatement/statement.pdf",
    #                                                                      output_directory,
    #                                                                      False)
    #
    # shutil.rmtree(temp_dir, ignore_errors=True)