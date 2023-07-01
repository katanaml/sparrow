from pdf2image import convert_from_path
import os
from tqdm import tqdm


class PDFConverter:
    def convert_to_jpg(self, pdf_path, jpg_path, dpi=300):
        # loop through all the pdf files in the folder ordered by name

        for pdf_file in tqdm(sorted((f for f in os.listdir(pdf_path) if not f.startswith(".")), key=str.lower)):
            # convert the pdf file to jpg
            pages = convert_from_path(pdf_path + '/' + pdf_file, dpi)
            # save pdf as jpg image or images
            if len(pages) == 0: 
                print(f"No pages read from pdf file: {pdf_file}")
            elif len(pages) == 1:
                pages[0].save(jpg_path + '/' + pdf_file.replace('.pdf', '') + '.jpg', 'JPEG')
            else:    
                # multi-page docs
                for i, page in enumerate(pages):
                    fname = pdf_file.replace('.pdf', '') + f"_pg{i+1}.jpg"
                    page.save(jpg_path + '/' + fname, 'JPEG')
