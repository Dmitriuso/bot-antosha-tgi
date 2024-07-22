import json
import requests
import traceback
import yaml

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.llms import HuggingFaceTextGenInference, LlamaCpp
from langchain_community.chat_models import ChatAnthropic

from langchain.chains import ConversationChain

from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory

from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG = ROOT / "config.yaml"

# load the config from YML file: if config is not commited in a project, you should add it manually
with open(CONFIG, 'r') as f:
    yaml_data = yaml.safe_load(f)

SG_HOST = yaml_data["sg_host"]
LOCAL_TGI_HOST = yaml_data["local_tgi_host"]

CPP_MODELS = ROOT/ "cpp_models"
CPP_MODEL_NAME = yaml_data["cpp_model"]
CPP_HOST = CPP_MODELS / CPP_MODEL_NAME

CLAUDE_TOKEN = yaml_data["claude_token"]

DEFAULT_PROMPT_EN = "Polite and respectful assistant provides concise and factual answers to the questions asked by a human, taking into account the previous conversation.\nConversation: {history}\nHuman: {input}\nAssistant:"

DEFAULT_PROMPT_FR = "L'assistant poli et respectueux répond aux questions posées par un humain en tenant compte de la conversation précédente.\nConversation: {history}\nHuman: {input}\nAssistant:"

STOP_SEQS = ["Human:", "Assistant:", "Human translation:", "AI:"]


class InferenceManager:
    def __init__(self, inf_mode: str, lang: str = "EN") -> None:
        self.inf_mode = inf_mode
        self.host = self.get_host()
        self.lang = lang
        self.default_sys_prompt = self.get_default_sys_prompt()

    def get_default_sys_prompt(self) -> str:
        match self.lang:
            case "EN":
                return DEFAULT_PROMPT_EN
            case "FR":
                return DEFAULT_PROMPT_FR
            case _:
                raise ValueError("Unsupported language")

    def get_host(self):
        match self.inf_mode:
            case "sg":
                return SG_HOST
            case "tgi":
                return LOCAL_TGI_HOST
            case "cpp":
                return CPP_HOST
            case "claude":
                return ""
            case _:
                raise ValueError("No such inference mode")


    # SensibleGenerative API inference
    def sg_request(self, qr: str = "what'up", ctxt: str = "", chat_history: list[tuple] = [("", "")]) -> str:
        try:
            headers = {
                "Content-Type": "application/json",
            }
            query = {
                "request": {
                    "lang": self.lang,
                    "context": ctxt,
                    "chat_history": chat_history,
                    "query": qr
                }
            }
            response = requests.post(self.host, headers=headers, json=query)
            json_response = json.loads(response.text)
            llm_response = json_response.get('results').get('answer')
            return llm_response
        except Exception:
            return traceback.print_exc() # "I don't know what to say..."
        
    # TGI / cpp / Claude inference
    def llm_request(self, qr: str, prompt: str | None = None, chat_history: list[tuple] = [("", "")]) -> str:
        try:
            if prompt == None:
                prompt = self._default_sys_prompt

            prompt_template = PromptTemplate(input_variables=["history", "input"], template=prompt)

            match self.inf_mode:
                case "tgi":
                    llm = HuggingFaceTextGenInference(
                            inference_server_url=self.host,
                            max_new_tokens=256,
                            top_k=60,
                            top_p=0.8,
                            typical_p=0.85,
                            temperature=0.65,
                            repetition_penalty=1.05,
                            timeout=40,
                            stop_sequences=STOP_SEQS,
                            # model_kwargs=dict(decoder_input_details=True),
                        )
                case "cpp":
                    llm = LlamaCpp(
                        model_path=str(self.host),
                        last_n_tokens_size=64,
                        max_tokens=1024,
                        # min_tokens=512,
                        temperature=0.85,
                        top_k=30,
                        top_p=0.8,
                        n_batch=16,
                        n_ctx=2048,
                        n_gpu_layers=33,
                        # f16_kv=True, # not sure I need this
                        # grammar_path=CPP_MODELS / "grammar.gbnf", # TODO: develop a proper grammar file
                        use_mlock=True,
                        verbose=True,
                    )
                case "claude":
                    llm = ChatAnthropic(anthropic_api_key=CLAUDE_TOKEN, model_name="claude-2.1", temperature=0.85, top_k=60, top_p=0.75)
                case _:
                    return "No such inference mode"
        except Exception:
            return traceback.print_exc()
        
        memory = ConversationBufferWindowMemory(human_prefix="Human", ai_prefix="AI", k=4)
        for i in chat_history:
            memory.save_context({"input": i[0]}, {"output": i[1]})
        conversational_chain = ConversationChain(
            llm=llm,
            prompt=prompt_template,
            memory=memory
        )
        
        llm_response = conversational_chain.predict(input=qr)
        return llm_response

    def infer(self, qr: str, prompt: str = DEFAULT_PROMPT_EN, chat_history: list[tuple] = [("", "")]):
        match self.inf_mode:
            case "sg":
                llm_response = self.sg_request(qr=qr, chat_history=chat_history)
            case "tgi" | "cpp" | "claude":
                llm_response = self.llm_request(qr=qr, prompt=prompt, chat_history=chat_history)
            case _:
                llm_response = "I don't know what to say: my powers are limited."
        
        return llm_response.lstrip(r"\n+")
