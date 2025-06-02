model_api_config=./model_api_configs/model_api_config_nopush.json
model_name=llama-3.3-70b-instruct
mas_model_name=llama-3.3-70b-instruct

# ==================================
TEST_DATASET_NAMES=("GSM-Hard" "MATH" "SciBench" "GPQA" "AQUA-RAT" "MMLU" "AIME-2024" "GPQA-Diamond" "MedQA" "MedMCQA")

METHOD_NAME_LIST=(
    vanilla
    self_consistency
    llm_debate
    autogen
    dylan
    agentverse
    macnet
    mad
)

for test_dataset_name in "${TEST_DATASET_NAMES[@]}"; do
    for method_name in "${METHOD_NAME_LIST[@]}"; do
        python evaluate.py --model_name $model_name \
        --model_api_config $model_api_config \
        --tested_method_name $method_name \
        --tested_mas_model_name $mas_model_name \
        --tested_dataset_name $test_dataset_name
    done
done