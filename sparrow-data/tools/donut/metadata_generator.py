from pathlib import Path
import json


class MetadataGenerator:
    def generate(self, data_dir):
        data_dir_path = Path(data_dir).joinpath("key")
        img_dir_path = Path(data_dir).joinpath("img")

        metadata_list = []

        for file_name in data_dir_path.glob("*.json"):
            with open(file_name, "r") as json_file:
                data = json.load(json_file)
                text = json.dumps(data)
                if img_dir_path.joinpath(f"{file_name.stem}.jpg").is_file():
                    metadata_list.append({
                        "text": text,
                        "file_name": f"{file_name.stem}.jpg"
                    })

        with open(Path(data_dir).joinpath("metadata.jsonl"), "w") as outfile:
            for entry in metadata_list:
                json.dump(entry, outfile)
                outfile.write("\n")