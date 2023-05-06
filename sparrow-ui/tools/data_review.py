import os
from natsort import natsorted
import json


def annotation_review():
    # get list of files in json directory
    processed_file_names = get_processed_file_names('../docs/json/')
    for file_name in processed_file_names:
        # open json file
        with open('../docs/json/' + file_name + '.json') as json_file:
            json_file_data = json.load(json_file)
            version = json_file_data['meta']['version']
            if version == "v0.1":
                print(file_name + " is v0.1")

def get_processed_file_names(dir_name):
    # get ordered list of files without file extension, excluding hidden files, with JSON extension only
    file_names = [os.path.splitext(f)[0] for f in os.listdir(dir_name) if
                    os.path.isfile(os.path.join(dir_name, f)) and not f.startswith('.') and f.endswith('.json')]
    file_names = natsorted(file_names)
    return file_names

def main():
    annotation_review()


if __name__ == '__main__':
    main()