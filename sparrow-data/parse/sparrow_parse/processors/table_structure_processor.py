from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from transformers import AutoModelForObjectDetection
from transformers import TableTransformerForObjectDetection
import torch
from PIL import Image
from torchvision import transforms
from PIL import ImageDraw
import os
import numpy as np
import easyocr


class TableDetector(object):
    def __init__(self):
        self.reader = easyocr.Reader(['en']) # this needs to run only once to load the model into memory

    class MaxResize(object):
        def __init__(self, max_size=800):
            self.max_size = max_size

        def __call__(self, image):
            width, height = image.size
            current_max_size = max(width, height)
            scale = self.max_size / current_max_size
            resized_image = image.resize((int(round(scale * width)), int(round(scale * height))))

            return resized_image

    def detect_table(self, file_path, options, local=True, debug=False):
        model, device = self.invoke_pipeline_step(
            lambda: self.load_table_detection_model(),
            "Loading table detection model...",
            local
        )

        outputs, image = self.invoke_pipeline_step(
            lambda: self.prepare_image(file_path, model, device),
            "Preparing image for table detection...",
            local
        )

        objects = self.invoke_pipeline_step(
            lambda: self.identify_tables(model, outputs, image),
            "Identifying tables in the image...",
            local
        )

        cropped_table = self.invoke_pipeline_step(
            lambda: self.crop_table(file_path, image, objects),
            "Cropping tables from the image...",
            local
        )

        structure_model = self.invoke_pipeline_step(
            lambda: self.load_table_structure_model(device),
            "Loading table structure recognition model...",
            local
        )

        structure_outputs = self.invoke_pipeline_step(
            lambda: self.get_table_structure(cropped_table, structure_model, device),
            "Getting table structure from cropped table...",
            local
        )

        table_data = self.invoke_pipeline_step(
            lambda: self.get_structure_cells(structure_model, cropped_table, structure_outputs),
            "Getting structure cells from cropped table...",
            local
        )

        self.invoke_pipeline_step(
            lambda: self.process_table_structure(table_data, cropped_table, file_path),
            "Processing structure cells...",
            local
        )


    def load_table_detection_model(self):
        model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection", revision="no_timm")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        return model, device

    def load_table_structure_model(self, device):
        structure_model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-structure-recognition-v1.1-all")
        structure_model.to(device)

        return structure_model

    def prepare_image(self, file_path, model, device):
        image = Image.open(file_path).convert("RGB")

        detection_transform = transforms.Compose([
            self.MaxResize(800),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        pixel_values = detection_transform(image).unsqueeze(0)
        pixel_values = pixel_values.to(device)

        with torch.no_grad():
            outputs = model(pixel_values)

        return outputs, image

    def identify_tables(self, model, outputs, image):
        id2label = model.config.id2label
        id2label[len(model.config.id2label)] = "no object"

        objects = self.outputs_to_objects(outputs, image.size, id2label)
        return objects

    def crop_table(self, file_path, image, objects):
        tokens = []
        detection_class_thresholds = {
            "table": 0.5,
            "table rotated": 0.5,
            "no object": 10
        }
        crop_padding = 10

        tables_crops = self.objects_to_crops(image, tokens, objects, detection_class_thresholds, padding=crop_padding)

        cropped_table = None

        if len(tables_crops) == 0:
            print("No tables detected.")
            return
        elif len(tables_crops) > 1:
            for i, table_crop in enumerate(tables_crops):
                cropped_table = table_crop['image'].convert("RGB")
                file_name_table = self.append_filename(file_path, f"table_{i}")
                cropped_table.save(file_name_table)
                break
        else:
            cropped_table = tables_crops[0]['image'].convert("RGB")

            file_name_table = self.append_filename(file_path, "table")
            cropped_table.save(file_name_table)

        return cropped_table

    # for output bounding box post-processing
    def box_cxcywh_to_xyxy(self, x):
        x_c, y_c, w, h = x.unbind(-1)
        b = [(x_c - 0.5 * w), (y_c - 0.5 * h), (x_c + 0.5 * w), (y_c + 0.5 * h)]
        return torch.stack(b, dim=1)

    def rescale_bboxes(self, out_bbox, size):
        img_w, img_h = size
        b = self.box_cxcywh_to_xyxy(out_bbox)
        b = b * torch.tensor([img_w, img_h, img_w, img_h], dtype=torch.float32)
        return b

    def outputs_to_objects(self, outputs, img_size, id2label):
        m = outputs.logits.softmax(-1).max(-1)
        pred_labels = list(m.indices.detach().cpu().numpy())[0]
        pred_scores = list(m.values.detach().cpu().numpy())[0]
        pred_bboxes = outputs['pred_boxes'].detach().cpu()[0]
        pred_bboxes = [elem.tolist() for elem in self.rescale_bboxes(pred_bboxes, img_size)]

        objects = []
        for label, score, bbox in zip(pred_labels, pred_scores, pred_bboxes):
            class_label = id2label[int(label)]
            if not class_label == 'no object':
                objects.append({'label': class_label, 'score': float(score),
                                'bbox': [float(elem) for elem in bbox]})

        return objects

    def objects_to_crops(self, img, tokens, objects, class_thresholds, padding=10):
        """
        Process the bounding boxes produced by the table detection model into
        cropped table images and cropped tokens.
        """

        table_crops = []
        for obj in objects:
            if obj['score'] < class_thresholds[obj['label']]:
                continue

            cropped_table = {}

            bbox = obj['bbox']
            bbox = [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding]

            cropped_img = img.crop(bbox)

            table_tokens = [token for token in tokens if self.iob(token['bbox'], bbox) >= 0.5]
            for token in table_tokens:
                token['bbox'] = [token['bbox'][0] - bbox[0],
                                 token['bbox'][1] - bbox[1],
                                 token['bbox'][2] - bbox[0],
                                 token['bbox'][3] - bbox[1]]

            # If table is predicted to be rotated, rotate cropped image and tokens/words:
            if obj['label'] == 'table rotated':
                cropped_img = cropped_img.rotate(270, expand=True)
                for token in table_tokens:
                    bbox = token['bbox']
                    bbox = [cropped_img.size[0] - bbox[3] - 1,
                            bbox[0],
                            cropped_img.size[0] - bbox[1] - 1,
                            bbox[2]]
                    token['bbox'] = bbox

            cropped_table['image'] = cropped_img
            cropped_table['tokens'] = table_tokens

            table_crops.append(cropped_table)

        return table_crops

    def get_table_structure(self, cropped_table, structure_model, device):
        structure_transform = transforms.Compose([
            self.MaxResize(1000),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        pixel_values = structure_transform(cropped_table).unsqueeze(0)
        pixel_values = pixel_values.to(device)

        with torch.no_grad():
            outputs = structure_model(pixel_values)

        return outputs

    def get_structure_cells(self, structure_model, cropped_table, outputs):
        structure_id2label = structure_model.config.id2label
        structure_id2label[len(structure_id2label)] = "no object"

        cells = self.outputs_to_objects(outputs, cropped_table.size, structure_id2label)

        return cells

    def process_table_structure(self, table_data, cropped_table, file_path):
        table_data = [cell for cell in table_data if cell['label'] != 'table spanning cell']
        table_data = [cell for cell in table_data if cell['score'] >= 0.9]

        # table, table column header, table row, table column
        # structure_cells = [cell for cell in structure_cells if cell['label'] == 'table']
        table_data = [cell for cell in table_data if cell['label'] == 'table column header'
                      or cell['label'] == 'table' or cell['label'] == 'table column']
        # structure_cells = [cell for cell in structure_cells if cell['label'] == 'table column header'
        #                    or cell['label'] == 'table column']
        # structure_cells = [cell for cell in structure_cells if cell['label'] == 'table column header'
        #                    or cell['label'] == 'table column' or cell['label'] == 'table row']
        # print(table_data)

        cropped_table_visualized = cropped_table.copy()
        draw = ImageDraw.Draw(cropped_table_visualized)

        header_cells = self.get_header_cell_coordinates(table_data)
        if header_cells is not None:
        # Output the coordinates of each cell
            print("Header cell coordinates:")
            print(header_cells)

            header_data = self.do_ocr_with_coordinates(header_cells, cropped_table)
            print("Header data:")
            print(header_data)

            for cell_data in header_cells['row0']:
                draw.rectangle(cell_data["cell"], outline="red")

            file_name_table_grid = self.append_filename(file_path, "table_grid_header")
            cropped_table_visualized.save(file_name_table_grid)

    def get_header_cell_coordinates(self, table_data):
        header_column = None
        columns = []

        # Separate header and columns
        for item in table_data:
            if item['label'] == 'table column header':
                header_column = item['bbox']
            elif item['label'] == 'table column':
                columns.append(item['bbox'])

        if not header_column:
            return None

        header_top = header_column[1]
        header_bottom = header_column[3]

        cells = []

        # Calculate cell coordinates based on header and column intersections
        for column in columns:
            cell_left = column[0]
            cell_right = column[2]
            cell_top = header_top
            cell_bottom = header_bottom

            cells.append({
                'cell': (cell_left, cell_top, cell_right, cell_bottom)
            })

        # Sort cells by the left coordinate (cell_left) to order them from left to right
        cells.sort(key=lambda x: x['cell'][0])

        header_row = {"row0": cells}

        return header_row

    def do_ocr_with_coordinates(self, cell_coordinates, cropped_table):
        data = {}
        max_num_columns = 0

        # Iterate over each row in cell_coordinates
        for row_key in cell_coordinates:
            row_text = []
            for cell in cell_coordinates[row_key]:
                # Crop cell out of image
                cell_image = cropped_table.crop(cell['cell'])
                cell_image_np = np.array(cell_image)

                # Apply OCR
                result = self.reader.readtext(cell_image_np)
                if result:
                    text = " ".join([x[1] for x in result])
                    row_text.append(text)
                else:
                    row_text.append("")  # If no text is detected, append an empty string

            if len(row_text) > max_num_columns:
                max_num_columns = len(row_text)

            data[row_key] = row_text

        print("Max number of columns:", max_num_columns)

        # Pad rows which don't have max_num_columns elements
        for row_key, row_data in data.items():
            if len(row_data) < max_num_columns:
                row_data += [""] * (max_num_columns - len(row_data))
            data[row_key] = row_data

        return data

    def append_filename(self, file_path, word):
        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{word}{ext}"
        return os.path.join(directory, new_filename)

    def iob(boxA, boxB):
        # Determine the coordinates of the intersection rectangle
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        # Compute the area of intersection rectangle
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

        # Compute the area of both the prediction and ground-truth rectangles
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

        # Compute the intersection over box (IoB)
        iob = interArea / float(boxAArea)

        return iob

    def invoke_pipeline_step(self, task_call, task_description, local):
        if local:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=False,
            ) as progress:
                progress.add_task(description=task_description, total=None)
                ret = task_call()
        else:
            print(task_description)
            ret = task_call()

        return ret


if __name__ == "__main__":
    table_detector = TableDetector()

    table_detector.detect_table("/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/invoice_1.jpg", None, local=True, debug=False)