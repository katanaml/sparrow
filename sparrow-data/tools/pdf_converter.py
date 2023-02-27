from pdf2image import convert_from_path
import os
from tqdm import tqdm


class PDFConverter:
    def convert_to_jpg(self, pdf_path, jpg_path):
        # loop through all the pdf files in the folder ordered by name

        for pdf_file in tqdm(sorted((f for f in os.listdir(pdf_path) if not f.startswith(".")), key=str.lower)):
            # convert the pdf file to jpg
            pages = convert_from_path(pdf_path + '/' + pdf_file, 300)
            # save the jpg file
            for page in pages:
                # this assumes that we work with single page docs, add a loop if you need to work with multi-page docs
                page.save(jpg_path + '/' + pdf_file.replace('.pdf', '') + '.jpg', 'JPEG')
