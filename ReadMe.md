# Simple Telegram Bot 

## Launch Bot App

### Temporary launch

`uvicorn main:app --reload --port 8001` : choose any open port.

### Constant launch

You will have to edit your own `.service` file in order to launch the bot app as a service in your operating system.

## Launch TGI endpoint

`bash run_tgi` : creates a Docker container for HF TGI endpoint, containing LLM for inference.