from pdf2image import convert_from_path
import os


class PDFConverter:
    def convert_to_jpg(self, pdf_path, jpg_path):
        # loop through all the pdf files in the folder ordered by name

        for pdf_file in sorted(os.listdir(pdf_path)):
            # convert the pdf file to jpg
            pages = convert_from_path(pdf_path + '/' + pdf_file, 300)
            # save the jpg file
            for page in pages:
                page.save(jpg_path + '/' + pdf_file.replace('.pdf', '') + '.jpg', 'JPEG')