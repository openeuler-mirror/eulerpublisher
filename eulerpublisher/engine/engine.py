import os
# import torch
import yaml
from openai import OpenAI
from eulerpublisher.utils.config import Config
from eulerpublisher.utils.logger import Logger
from eulerpublisher.utils.constants import MODEL_DIR, KNOWLEDGE_DIR, INDEX_DIR
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM, LlamaTokenizer
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate


class Engine():
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        offline_path = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2")
        try:
            self.embedding_model = HuggingFaceEmbeddings(model_name=offline_path)
        except:
            self.logger.warning("Failed to load offline embedding model, switching to online model")
            # load online embedding model
            self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        self.vectors = {}

        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)

        # transfer yaml to text
        def preprocess_yaml(knowledge_path):
            requires=[]
            with open(knowledge_path, "r", encoding="utf-8") as f:
                knowledge = yaml.safe_load(f)
            for item in knowledge.get("knowledge", []):
                name = item.get("name", "unknown")
                if name in ["unknown", "python"]:
                    continue
                for v in item.get("versions", []):
                    version = v.get("version", "unknown")
                    # requires
                    if "requires" in v:
                        for req_key, req_vals in v["requires"].items():
                            tmp = f"{name}={version} requires "
                            if all(rv.startswith(">=") or rv.startswith("<=") for rv in req_vals):
                                tmp += " and ".join([f"{req_key}{rv}" for rv in req_vals])
                            else:
                                tmp += req_key + " in [ " + ", ".join(req_vals) + "]"
                            requires.append(tmp)
            return requires

        for key in ["requires", "customized"]:
            index_path = f"{INDEX_DIR}/{key}_faiss_index"
            if os.path.exists(index_path):
                self.vectors[key] = FAISS.load_local(index_path, self.embedding_model, 
                allow_dangerous_deserialization=True)
            elif key != "customized":
                knowledge_path = os.path.join(KNOWLEDGE_DIR, "knowledge.yaml")
                if not os.path.exists(knowledge_path):
                    self.logger.error(f"No knowledge file found at {knowledge_path}")
                    continue
                knowledge = preprocess_yaml(knowledge_path)
                docs = [Document(page_content=text) for text in knowledge]
                vectorstore = FAISS.from_documents(docs, self.embedding_model)
                vectorstore.save_local(index_path)
                self.vectors[key] = vectorstore

        self.token = self.config.get("global", "llm_token")
        self.logger.info("Engine initialized")

    def analyze_layers(self, layers, model_name, stream=False):
        # Step 1: RAG
        layer_detail = [f"{layer['name']}={layer['version']}" for layer in layers]
        query = " ".join(layer_detail)

        retrieved_docs = []

        vectorstore = self.vectors["requires"]
        docs = vectorstore.similarity_search(query, k=2*len(layers))
        retrieved_docs += [doc.page_content for doc in docs]

        if "customized" in self.vectors:
            vectorstore = self.vectors["customized"]
            docs = vectorstore.similarity_search(query, k=3*len(layers))
            retrieved_docs += [doc.page_content for doc in docs]

        # Step 2: build prompt
        template = (
            "你是一名专业的软件依赖分析专家。\n"
            "请基于下列输入完成三个任务：\n"
            "1) 检测提供的软件栈中是否存在版本冲突,仅需要考虑软件层中出现过的软件及版本；\n"
            "2) 分析哪些层可以合并或拆分。\n"
            "  例如：某些软件之间存在替代关系，安装其中一个即可满足需求，这种情况下可以合并这些层以减少冗余。\n"
            "3) 分析是否可以优化构建顺序。\n"
            "  例如：软件间存在requires关系，被需要的软件应优先安装\n"
            "输入内容：\n"
            "软件层(列表中每个元素格式: name=version)，以下是需要安装的软件，考虑冲突或优化时仅针对这些软件：\n"
            "{layers_text}\n\n"
            "牢记软件层里出现的软件，这些软件之后需要在layers和new_layers中体现出来。\n\n"
            "以下不是软件层的软件，而是检索到的参考依赖信息文档:\n"
            "{docs_text}\n\n"
            "请严格按照以下 JSON 格式输出结果，确保可直接解析：\n"
            "{{\n"
            "  \"conflict\": true/false,  // 是否存在版本冲突\n"
            "  \"requires\": [\"string\",\"string\",...],  // 如果有冲突，写出检索文档中的原文(优先requires信息,如果检索到requires信息,则不再需要相同的conflicts信息)，否则为空\n"
            "  \"detail\": \"string\",  // 如果有优化建议，输出具体内容\n"
            "  \"layers\": [\"软件名=版本号\", \"软件名=版本号\", ...],  // 优化前的软件层\n"
            "  \"new_layers\": [\"软件名=版本号\", \"软件名=版本号\", ...]  // 优化后的软件层，基于优化前的软件层，不考虑layers中没有出现过的软件\n"
            "  \"change\": true/false,  // layers 和 new_layers 是否完全相同，完全相同返回false\n"
            "}}\n\n"
            "注意：\n"
            "1. 严格遵循 JSON 格式，不能出现多余文字、注释或格式错误。\n"
            "2. 所有字段必须存在，即使没有内容也要输出空数组或空字符串。\n"
            "3. layers 和 new_layers 中每个元素格式必须为 '软件名=版本号'，方便后续解析。\n"
            "4. 确保解析时无需额外处理即可直接使用。\n"
            "5. 只需要考虑软件层出现过的软件，其他软件不用安装，也不需要考虑未来扩展。\n"
            "6. 没有直接、明确的冲突存在，就默认为没有冲突。\n"
            "7. 没有冲突时，重点考虑构建顺序、层合并等优化建议。\n"
            "8. 优化构建顺序时，不要改动 OpenEuler 的顺序。\n"
        )

        prompt = PromptTemplate(
            input_variables=["layers_text", "docs_text"],
            template=template,
        )
        layers_text ="["+",".join(layer_detail)+"]"
        docs_text = "\n".join(retrieved_docs)
        final_prompt = prompt.format(layers_text=layers_text, docs_text=docs_text)

        # Step 3: LLM
        client = OpenAI(api_key=self.token, base_url="https://api.siliconflow.cn/v1")

        response = client.chat.completions.create(
            model=model_name,
            messages=[{'role': 'user', 'content': final_prompt}],
            stream=False
        )
        if stream is False:
            return response.choices[0].message.content
        else:
            return response

    def parse_pdf(self, file, model_name="Qwen/Qwen3-Coder-30B-A3B-Instruct", stream=False):
        loader = PyPDFLoader(file.name)
        docs = loader.load()
        pdf_text = "\n".join([doc.page_content for doc in docs])

        client = OpenAI(api_key=self.token, base_url="https://api.siliconflow.cn/v1")
        prompt = (
            "你是一名专业的软件依赖分析专家。"
            "请仔细阅读以下文本内容，精准提取所有与软件/库版本冲突、需求相关的信息。"
            "要求：\n"
            "1. 首先识别文本涉及的软件或库名称及版本号。\n"
            "2. 精确检索并提取所有包含版本冲突或需求的句子或段落，输出对应原文\n"
            "3. 输出格式严格遵循：<软件/库>=<版本号>：<检索到的原文>\n"
            "   - 名称和版本号应从文档标题、头部、或文中首次出现的软件/库及其版本中提取。\n"
            "4. 每条信息单独一行，保持原文顺序。\n"
            "5. 如果未找到任何相关句子或段落，无需任何返回。\n"
            "6. 不输出无关内容或解释说明。\n"
            "文本内容如下：\n"
            f"{pdf_text}"
        )
        # print(pdf_text)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            stream=False
        )
        if stream:
            for chunk in response:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                if chunk.choices[0].delta.reasoning_content:
                    print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
            return

        response_text = response.choices[0].message.content
        lines = [line.strip() for line in response_text.split("\n") if line.strip()]
        docs = [Document(page_content=line) for line in lines]
        
        index_path = f"{INDEX_DIR}/customized_faiss_index"
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(index_path, self.embedding_model, 
                                        allow_dangerous_deserialization=True)
            vectorstore.add_documents(docs)
        else:
            vectorstore = FAISS.from_documents(docs, self.embedding_model)

        vectorstore.save_local(index_path)
        self.vectors["customized"] = vectorstore