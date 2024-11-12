from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer
from rich import print
import os
import shutil


class VLLMExtractor(object):
    def __init__(self):
        pass

    def run_inference(self,
                      model_inference_instance,
                      input_data,
                      generic_query=False,
                      debug_dir=None,
                      debug=False,
                      mode=None):
        if generic_query:
            input_data[0]["text_input"] = "retrieve document data. return response in JSON format"

        if debug:
            print("Input Data:", input_data)

        results_array = []

        if self.is_pdf(input_data[0]["file_path"]):
            pdf_optimizer = PDFOptimizer()
            num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(input_data[0]["file_path"],
                                                                                 debug_dir,
                                                                                 True)

            # Run inference on each page
            for page_num, output_file in enumerate(output_files):
                input_data[0]["file_path"] = output_file
                if debug:
                    print(f"Running inference on page {page_num + 1}...")

                # Run inference on the page
                result = model_inference_instance.inference(input_data, mode)
                results_array.append(result)

            shutil.rmtree(temp_dir, ignore_errors=True)
            return results_array, num_pages

        result = model_inference_instance.inference(input_data)
        results_array.append(result)

        return results_array, 1

    def is_pdf(self, file_path):
        return file_path.lower().endswith('.pdf')

if __name__ == "__main__":
    # run locally: python -m sparrow_parse.extractors.vllm_extractor

    extractor = VLLMExtractor()

    # # export HF_TOKEN="hf_"
    # config = {
    #     "method": "huggingface",  # Could be 'huggingface' or 'local_gpu'
    #     "hf_space": "katanaml/sparrow-qwen2-vl-7b",
    #     "hf_token": os.getenv('HF_TOKEN'),
    #     # Additional fields for local GPU inference
    #     # "device": "cuda", "model_path": "model.pth"
    # }
    #
    # # Use the factory to get the correct instance
    # factory = InferenceFactory(config)
    # model_inference_instance = factory.get_inference_instance()
    #
    # input_data = [
    #     {
    #         "file_path": "/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/oracle_10k_2014_q1_small.pdf",
    #         "text_input": "retrieve {\"table\": [{\"description\": \"str\", \"latest_amount\": 0, \"previous_amount\": 0}]}. return response in JSON format"
    #     }
    # ]
    #
    # # Now you can run inference without knowing which implementation is used
    # results_array, num_pages = extractor.run_inference(model_inference_instance, input_data, generic_query=False,
    #                                  debug_dir="/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/",
    #                                  debug=True,
    #                                  mode="static")
    #
    # for i, result in enumerate(results_array):
    #     print(f"Result for page {i + 1}:", result)
    # print(f"Number of pages: {num_pages}")