import json
import requests

from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceTextGenInference
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
    
prompt = "You are an AI epitome of a Russian intellectual, speaking in Chekhovian style with subtle humor and irony. You answer your interviewer questions at ease, and there are no taboo topics for you.\nConversation: {history}\nInterviewer: {input}\nAI:"

PROMPT_TEMPLATE = PromptTemplate(input_variables=["history", "input"], template=prompt)

STOP_SEQS = ["Interviewer:", "AI:", "Interviewer translation:"]


def local_tgi_request(host: str, qr: str, chat_history: list[tuple] = [("", "")]) -> str:
    llm = HuggingFaceTextGenInference(
            inference_server_url=host,
            max_new_tokens=512,
            # top_k=40,
            top_p=0.7,
            typical_p=0.75,
            temperature=0.75,
            repetition_penalty=1.1,
            timeout=6000,
            stop_sequences=STOP_SEQS,
            # model_kwargs=dict(decoder_input_details=True),
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
