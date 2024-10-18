import gradio as gr

def run_inference(image, text_input, key_input):
    pass

css = """
  #output {
    height: 500px; 
    overflow: auto; 
    border: 1px solid #ccc; 
  }
"""

with gr.Blocks(css=css, theme=gr.themes.Ocean()) as demo:
    # gr.Markdown(DESCRIPTION)
    with gr.Tab(label="Sparrow UI"):
        with gr.Row():
            with gr.Column():
                input_img = gr.Image(label="Input Document Image")
                query_input = gr.Textbox(label="Query")
                key_input = gr.Textbox(label="Sparrow Key", type="password")
                submit_btn = gr.Button(value="Submit", variant="primary")
            with gr.Column():
                output_text = gr.Textbox(label="Response")

        submit_btn.click(run_inference, [input_img, query_input, key_input], [output_text])

        gr.Markdown(
            """
            ---
            <p style="text-align: center;">
            Visit <a href="https://katanaml.io/" target="_blank">Katana ML</a> for more details.
            </p>
            """
        )

demo.queue(api_open=False)
demo.launch(debug=True)