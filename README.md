# Simple Telegram bot with LLM under the hood 

## Setup

It is recommended to use conda to create a new environment and install all the dependencies.

```
conda create -n llm-bot python=3.12.9
conda activate llm-bot
pip install -r requirements.txt
```

## Launch Bot App

### Temporary launch

`uvicorn main:app --reload --port 28000` : choose any open port (you can check those with `ss -tulnp`)

### System service with systemd

#### OPS side

First, let's create a script `./run_service` that would activate our local environment (`conda`, in my case) and launch a web server (`uvicorn`, in my case):

```
source <path to conda>/etc/profile.d/conda.sh \
&& conda activate <conda environment name> \
&& cd <path to the project>/bot-antosha-tgi \
&& bash run
```

`./run` being the script that launches the web server:

```
#!/bin/bash

# Runs the Telegram bot.
echo "Starting the Telegram bot..."
uvicorn main:app
  --reload
  --port 28000 # or any other port
```

#### systemd

Now, you let's edit your own `.service` file in order to launch the bot app as a service in your operating system. Here is an example:

```
[Unit]
Description=telegram-bot

[Service]
Type=simple
ExecStart=<path to the executable script>
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

In order to launch it on user's level, you should copy the `.service` file to `~/.config/systemd/user`. Then, do as follows:

`sudo systemctl daemon-reload` : reload the daemon in order to take your service into account

`systemctl --user enable telegram-bot.service` : enable the service, so that it would run even after reboot

`systemctl --user start telegram-bot.service` : start the service

You can the check the status of your service using `systemctl --user status telegram-bot.service`.


## TGI endpoint

If you chose to use HuggingFace TGI endpoint as your LLM inference source, you have a script example in `run_tgi.sh`.