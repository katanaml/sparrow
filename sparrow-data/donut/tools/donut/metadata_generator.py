from pathlib import Path
import json
import cv2


class DonutMetadataGenerator:
    def generate(self, data_dir, files_list, split):
        base_img_dir_path = Path(data_dir).joinpath("key/img")
        img_dir_path = Path(data_dir).joinpath("img/" + split)

        metadata_list = []

        for file_name in files_list:
            file_name_img = base_img_dir_path.joinpath(f"{file_name.stem}.jpg")
            img = cv2.imread(str(file_name_img))
            cv2.imwrite(str(img_dir_path.joinpath(f"{file_name.stem}.jpg")), img)

            with open(file_name, "r") as json_file:
                data = json.load(json_file)
                line = {"gt_parse": data}
                text = json.dumps(line)
                if img_dir_path.joinpath(f"{file_name.stem}.jpg").is_file():
                    metadata_list.append({
                        "ground_truth": text,
                        "file_name": f"{file_name.stem}.jpg"
                    })

        with open(Path(img_dir_path).joinpath("metadata.jsonl"), "w") as outfile:
            for entry in metadata_list:
                json.dump(entry, outfile)
                outfile.write("\n")