#!/bin/bash

container_name=generative_tgi
model=Qwen/Qwen2-1.5B-Instruct # little LLM for example purposes
volume=/llms/$model

max_batch_prefill_tokens=1024
max_batch_total_tokens=2048
max_concurrent_requests=2
max_input_length=1024
max_total_tokens=1536


export CUDA_VISIBLE_DEVICES=0

docker rm -f $container_name

docker run --name $container_name --restart unless-stopped --gpus all --shm-size 1g -p 2300:80 \
  -v $PWD$volume:/data ghcr.io/huggingface/text-generation-inference:1.4 \
  --model-id $model \
  --max-stop-sequences 4 \
  --max-best-of 4 \
  --validation-workers 4 \
  --max-concurrent-requests $max_concurrent_requests \
  --max-input-length $max_input_length \
  --max-total-tokens $max_total_tokens \
  --max-batch-prefill-tokens $max_batch_prefill_tokens \
  --max-batch-total-tokens $max_batch_total_tokens \
  --waiting-served-ratio 1.3 \
  --cuda-memory-fraction 1.0 \
  # --trust-remote-code \
  # --quantize bitsandbytes-nf4 \
  # --env \
  # --sharded true \
  # --num-shard 2 \
  # for multiple GPUs use


# docker run -d --name $container_name --gpus all --shm-size 1g -p 2300:80 -v $PWD/shared:$PWD/shared \
# -v $PWD$volume:/data ghcr.io/huggingface/text-generation-inference:1.4 \
# --model-id $PWD/shared/neural-chat-7b-v3-1-sft-trl/first_try \