#! /bin/bash

export VLLM_ATTENTION_BACKEND=FLASHINFER


ROOT_DIR=$(dirname $(dirname $(realpath $0)))
MODELS_DIR=$ROOT_DIR/models

export CUDA_VISIBLE_DEVICES=0

container="vllm-qwen25-14b-instruct-1m"

docker rm -f $container

MODEL_NAME="Qwen/Qwen2.5-14B-Instruct-1M"
HF_HUB_TOKEN=""

docker run --gpus '"device=0,1"' \
    --name $container --restart unless-stopped \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_HUB_TOKEN" \
    -p 2301:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --device cuda \
    --tensor-parallel-size 2 \
    --model $MODEL_NAME \
    --dtype bfloat16 \
    --chat-template-content-format "string" \
    --max_model_len 16384 \
    # --enable-reasoning \
    # --reasoning-parser deepseek_r1