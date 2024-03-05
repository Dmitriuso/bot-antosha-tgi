import json
import requests

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.llms import HuggingFaceTextGenInference, LlamaCpp
from langchain_community.chat_models import ChatAnthropic

from langchain.chains import ConversationChain

from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory

### SensibleGenerative API inference

def sg_request(host: str, qr: str = "what'up", lang: str = "en", ctxt: str = "", chat_history: list[tuple] = [("", "")]) -> str:
    try:
        headers = {
            "Content-Type": "application/json",
        }
        query = {
            "request": {
                "lang": lang,
                "context": ctxt,
                "chat_history": chat_history,
                "query": qr
            }
        }
        response = requests.post(host, headers=headers, json=query)
        json_response = json.loads(response.text)
        llm_response = json_response.get('results').get('answer')
        return llm_response
    except Exception:
        return "I don't know what to say..."
    


### Local TGI host inference
    
prompt = "Polite and respectful AI replies in English to the questions asked by a human taking the previous conversation into account.\nConversation: {history}\nHuman: {input}\nAI:"

PROMPT_TEMPLATE = PromptTemplate(input_variables=["history", "input"], template=prompt)

STOP_SEQS = ["Human:", "AI:", "Human translation:"]


def local_tgi_request(host: str, qr: str, chat_history: list[tuple] = [("", "")]) -> str:
    llm = HuggingFaceTextGenInference(
            inference_server_url=host,
            max_new_tokens=512,
            top_k=60,
            top_p=0.8,
            typical_p=0.85,
            temperature=0.65,
            repetition_penalty=1.03,
            timeout=20,
            stop_sequences=STOP_SEQS,
            # model_kwargs=dict(decoder_input_details=True),
        )
    
    memory = ConversationBufferWindowMemory(human_prefix="Human", ai_prefix="AI", k=4)
    for i in chat_history:
        memory.save_context({"input": i[0]}, {"output": i[1]})
    conversational_chain = ConversationChain(
        llm=llm,
        prompt=PROMPT_TEMPLATE,
        memory=memory
    )
    
    llm_response = conversational_chain.predict(input=qr)
    return llm_response


# request to local LlamaCpp model
def local_llamacpp_request(model_path: str, qr: str, chat_history: list[tuple] = [("", "")]) -> str:
    llm = LlamaCpp(
        model_path=model_path,
        last_n_tokens_size=64,
        max_tokens=512,
        # min_tokens=512,
        temperature=0.45,
        top_k=60,
        top_p=0.8,
        n_batch=8,
        n_ctx=4096,
        n_gpu_layers=43,
        verbose=True
    )

    memory = ConversationBufferWindowMemory(human_prefix="Interviewer", ai_prefix="AI", k=4)
    for i in chat_history:
        memory.save_context({"input": i[0]}, {"output": i[1]})
    conversational_chain = ConversationChain(
        llm=llm,
        prompt=PROMPT_TEMPLATE,
        memory=memory
    )
    
    llm_response = conversational_chain.predict(input=qr)
    return llm_response



# Request towards an Anthropic model (Claude)
def claude_request(token: str, qr: str, chat_history: list[tuple] = [("", "")]) -> str:
    llm = ChatAnthropic(anthropic_api_key=token, model_name="claude-instant-1.2", temperature=0.85, top_k=60, top_p=0.75)

    prompt = "Honest and truthful AI.\nConversation: {history}\nInterviewer: {input}\nAI:"

    PROMPT_TEMPLATE = PromptTemplate(input_variables=["history", "input"], template=prompt)

    memory = ConversationBufferWindowMemory(human_prefix="Human", ai_prefix="AI", k=4)
    for i in chat_history:
        memory.save_context({"input": i[0]}, {"output": i[1]})
    conversational_chain = ConversationChain(
        llm=llm,
        prompt=PROMPT_TEMPLATE,
        memory=memory
    )
    
    llm_response = conversational_chain.predict(input=qr)

    return llm_response