import json
import os

import datasets

logger = datasets.logging.get_logger(__name__)

_CITATION = """\
@article{park2019cord,
  title={CORD: A Consolidated Receipt Dataset for Post-OCR Parsing},
  author={Park, Seunghyun and Shin, Seung and Lee, Bado and Lee, Junyeop and Surh, Jaeheung and Seo, Minjoon and Lee, Hwalsuk}
  booktitle={Document Intelligence Workshop at Neural Information Processing Systems}
  year={2019}
}
"""

_DESCRIPTION = """\
https://huggingface.co/datasets/katanaml/cord
"""


def normalize_bbox(bbox, width, height):
    return [
        int(1000 * (bbox[0] / width)),
        int(1000 * (bbox[1] / height)),
        int(1000 * (bbox[2] / width)),
        int(1000 * (bbox[3] / height)),
    ]


class CordConfig(datasets.BuilderConfig):
    """BuilderConfig for CORD"""

    def __init__(self, **kwargs):
        """BuilderConfig for CORD.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(CordConfig, self).__init__(**kwargs)


class Cord(datasets.GeneratorBasedBuilder):
    """CORD dataset."""

    BUILDER_CONFIGS = [
        CordConfig(name="cord", version=datasets.Version("1.0.0"), description="CORD dataset"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Sequence(datasets.Value("string")),
                    "bboxes": datasets.Sequence(datasets.Sequence(datasets.Value("int64"))),
                    "ner_tags": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=['O',
                                   'menu.cnt',
                                   'menu.discountprice',
                                   'menu.nm',
                                   'menu.num',
                                   'menu.price',
                                   'menu.sub_cnt',
                                   'menu.sub_nm',
                                   'menu.sub_price',
                                   'menu.unitprice',
                                   'sub_total.discount_price',
                                   'sub_total.etc',
                                   'sub_total.service_price',
                                   'sub_total.subtotal_price',
                                   'sub_total.tax_price',
                                   'total.cashprice',
                                   'total.changeprice',
                                   'total.creditcardprice',
                                   'total.emoneyprice',
                                   'total.menuqty_cnt',
                                   'total.menutype_cnt',
                                   'total.total_etc',
                                   'total.total_price']
                        )
                    ),
                    "image_path": datasets.Value("string"),
                }
            ),
            supervised_keys=None,
            homepage="https://huggingface.co/datasets/katanaml/cord",
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        downloaded_file = dl_manager.download_and_extract(
            "https://huggingface.co/datasets/katanaml/cord/resolve/main/dataset.zip")

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN, gen_kwargs={"filepath": f"{downloaded_file}/CORD/train/"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST, gen_kwargs={"filepath": f"{downloaded_file}/CORD/test/"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION, gen_kwargs={"filepath": f"{downloaded_file}/CORD/dev/"}
            ),
        ]

    def _generate_examples(self, filepath):
        guid = -1

        replacing_labels = ['menu.etc', 'menu.itemsubtotal', 'menu.sub_etc', 'menu.sub_unitprice', 'menu.vatyn',
                            'void_menu.nm', 'void_menu.price', 'sub_total.othersvc_price']

        logger.info("⏳ Generating examples from = %s", filepath)
        ann_dir = os.path.join(filepath, "json")
        img_dir = os.path.join(filepath, "image")

        for file in sorted(os.listdir(ann_dir)):
            guid += 1
            tokens = []
            bboxes = []
            ner_tags = []

            file_path = os.path.join(ann_dir, file)
            with open(file_path, "r", encoding="utf8") as f:
                data = json.load(f)

            image_path = os.path.join(img_dir, file)
            image_path = image_path.replace("json", "png")

            width, height = data["meta"]["image_size"]["width"], data["meta"]["image_size"]["height"]

            for item in data["valid_line"]:
                for word in item['words']:
                    # get word
                    txt = word['text']

                    # get bounding box
                    x1 = word['quad']['x1']
                    y1 = word['quad']['y1']
                    x3 = word['quad']['x3']
                    y3 = word['quad']['y3']

                    box = [x1, y1, x3, y3]
                    box = normalize_bbox(box, width=width, height=height)

                    # skip empty word
                    if len(txt) < 1:
                        continue

                    tokens.append(txt)
                    bboxes.append(box)

                    if item['category'] in replacing_labels:
                        ner_tags.append('O')
                    else:
                        ner_tags.append(item['category'])

            yield guid, {"id": str(guid), "tokens": tokens, "bboxes": bboxes, "ner_tags": ner_tags,
                         "image_path": image_path}
