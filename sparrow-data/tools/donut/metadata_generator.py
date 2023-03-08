from pathlib import Path
import json


class DonutMetadataGenerator:
    def generate(self, data_dir):
        data_dir_path = Path(data_dir).joinpath("key")
        img_dir_path = Path(data_dir).joinpath("img/train")

        metadata_list = []

        for file_name in data_dir_path.glob("*.json"):
            with open(file_name, "r") as json_file:
                data = json.load(json_file)
                text = json.dumps(data)
                if img_dir_path.joinpath(f"{file_name.stem}.jpg").is_file():
                    metadata_list.append({
                        "ground_truth": text,
                        "file_name": f"{file_name.stem}.jpg"
                    })

        with open(Path(img_dir_path).joinpath("metadata.jsonl"), "w") as outfile:
            for entry in metadata_list:
                json.dump(entry, outfile)
                outfile.write("\n")