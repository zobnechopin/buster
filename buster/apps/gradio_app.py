import os
import pathlib

import gradio as gr

from buster.apps.bot_configs import available_configs
from buster.busterbot import Buster, BusterConfig
from buster.retriever import Retriever
from buster.utils import download_db, get_retriever_from_extension

DEFAULT_CONFIG = "huggingface"
DB_URL = "https://huggingface.co/datasets/jerpint/buster-data/resolve/main/documents.db"

# Download the db...
documents_filepath = download_db(db_url=DB_URL, output_dir="./data")
retriever: Retriever = get_retriever_from_extension(documents_filepath)(documents_filepath)

# initialize buster with the default config...
default_cfg: BusterConfig = available_configs.get(DEFAULT_CONFIG)
buster = Buster(cfg=default_cfg, retriever=retriever)


def chat(question, history, bot_source):
    history = history or []
    cfg = available_configs.get(bot_source)
    buster.update_cfg(cfg)
    answer = buster.process_input(question)

    # formatting hack for code blocks to render properly every time
    answer = answer.replace("```", "\n```\n")

    history.append((question, answer))
    return history, history


block = gr.Blocks(css="#chatbot .overflow-y-auto{height:500px}")

with block:
    with gr.Row():
        gr.Markdown("<h3><center>Buster 🤖: A Question-Answering Bot for open-source libraries </center></h3>")

    doc_source = gr.Dropdown(
        choices=sorted(list(available_configs.keys())),
        value=DEFAULT_CONFIG,
        interactive=True,
        multiselect=False,
        label="Source of Documentation",
        info="The source of documentation to select from",
    )

    chatbot = gr.Chatbot()

    with gr.Row():
        message = gr.Textbox(
            label="What's your question?",
            placeholder="What kind of model should I use for sentiment analysis?",
            lines=1,
        )
        submit = gr.Button(value="Send", variant="secondary").style(full_width=False)

    examples = gr.Examples(
        # TODO: seems not possible (for now) to update examples on change...
        examples=[
            "What kind of models should I use for images and text?",
            "When should I finetune a model vs. training it form scratch?",
            "Can you give me some python code to quickly finetune a model on my sentiment analysis dataset?",
        ],
        inputs=message,
    )

    gr.Markdown(
        """This simple application uses GPT to search the huggingface 🤗 transformers docs and answer questions.
    For more info on huggingface transformers view the [full documentation.](https://huggingface.co/docs/transformers/index)."""
    )

    gr.HTML("️<center> Created with ❤️ by @jerpint and @hadrienbertrand")

    state = gr.State()
    agent_state = gr.State()

    submit.click(chat, inputs=[message, state, doc_source], outputs=[chatbot, state])
    message.submit(chat, inputs=[message, state, doc_source], outputs=[chatbot, state])


block.launch(debug=True)
