model_api_config=./model_api_configs/model_api_config.json
model_name=gpt-4o-mini-2024-07-18

# ==================================
# TEST_DATASET_NAMES=("GSM-Hard" "MATH" "SciBench" "GPQA" "AQUA-RAT" "MMLU" "AIME-2024" "GPQA-Diamond" "MedQA" "MedMCQA")
# METHOD_NAME_LIST=(
#     vanilla
#     self_consistency
#     llm_debate
#     autogen
#     dylan
#     agentverse
#     macnet
#     mad
# )
TEST_DATASET_NAMES=("HumanEval")
METHOD_NAME_LIST=(mapcoder)

for test_dataset_name in "${TEST_DATASET_NAMES[@]}"; do
    for method_name in "${METHOD_NAME_LIST[@]}"; do
        python inference.py --method_name $method_name --model_name $model_name --test_dataset_name $test_dataset_name --model_api_config $model_api_config --debug
    done
done
