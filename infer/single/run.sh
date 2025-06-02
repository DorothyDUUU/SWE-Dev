#!/bin/bash

# Inference for single agent
python infer/single/single_agent_infer.py \
--model_name "gpt-4o" \
--dataset_path "data/test" \
--num_workers 10 \
--api_base_url "http://123.129.219.111:3000/v1" \
--api_key "sk-SqIObthbSxQum6HLl2ynolu9ieut8RuHveTii24Ha5hUQZ0O" \
--level "easy" \
--pass_k 3 \
--save_name "test_easy"

# # Evaluate the inference results
# python SWE-Dev-dataset/infer/single/single_evaluation_passk.py\
# --model_name "gpt-4o" \
# --level "easy" \
# --source_path  "SWE-Dev-dataset/data/test"\
# --pass_k 3 \
# --save_name "test"\
# --num_workers 100\