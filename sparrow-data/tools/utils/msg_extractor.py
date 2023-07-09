import extract_msg
import os


def save_pdf_from_msg(folder_path, save_path):
    counter = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.msg'):
            msg_file_path = os.path.join(folder_path, filename)
            msg = extract_msg.Message(msg_file_path)

            for att in msg.attachments:
                if att.longFilename is not None and att.longFilename.lower().endswith('.pdf'):
                    counter += 1
                    att.save(customPath=save_path)

    print('All PDF attachments have been saved.')
    print(f'Total number of PDFs: {counter}')


def main():
    folder_path = 'in_path'  # replace with your .msg files directory
    save_path = 'out_path'  # replace with the directory where you want to save the PDFs
    save_pdf_from_msg(folder_path, save_path)


if __name__ == "__main__":
    main()
