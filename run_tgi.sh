#!/bin/bash

container_name=generative_tgi
model=lmsys/vicuna-7b-v1.5-16k
volume=/llms/$model


export CUDA_VISIBLE_DEVICES=0

docker rm -f $container_name

docker run -d --name $container_name --gpus all --shm-size 1g -p 2300:80 \
  -v $PWD$volume:/data ghcr.io/huggingface/text-generation-inference:1.3.4 \
  --model-id $model \
  --max-stop-sequences 4 \
  --max-best-of 4 \
  --validation-workers 4 \
  --max-concurrent-requests 2 \
  --max-input-length 4096 \
  --max-total-tokens 4608 \
  --max-batch-prefill-tokens 4608 \
  --max-batch-total-tokens 4608 \
  --waiting-served-ratio 1.3 \
  --env \
  --trust-remote-code \
  # --sharded true \
  # --num-shard 2 \
  # --quantize eetq \
  # for multiple GPUs use



  # docker run -d --name $container_name --gpus all --shm-size 1g -p 2300:80 -v $PWD/shared:$PWD/shared \
  # -v $PWD$volume:/data ghcr.io/huggingface/text-generation-inference:1.3.4 \
  # --model-id $PWD/shared/neural-chat-7b-v3-1-sft-trl/first_try \