from .mas_base import MAS
from .cot import CoT
from .self_consistency import SelfConsistency, SelfConsistency_package
from .llm_debate import LLMDebate, LLMDebate_MATH, LLMDebate_GSM, LLMDebate_MMLU,LLMDebate_package
from .autogen import AutoGen
# from .chatdev import ChatDev_SRDD
from .mapcoder import MapCoder_HumanEval, MapCoder_MBPP,MapCoder_Package
# from .DyLAN import DyLAN_Main, DyLAN_MMLU, DyLAN_Humaneval, DyLAN_MATH
# from .medagents import MedAgents
from .agentverse import Agentverse_HumanEval, Agentverse_MGSM, Agentverse_MAIN,Agentverse_Package,Agentverse_Package1
# from .evomac import EvoMAC
# from .macnet import Macnet, Macnet_SRDD
from .mad import MAD, MAD_Package
from .metagpt import MetaGPT, MetaGPT_Package
# from .mav import MAV_GPQA, MAV_HumanEval, MAV, MAV_MATH, MAV_MMLU
from .self_refine import SelfRefineMain, SelfRefineMath, SelfRefinePackage
from .reflexion import  ReflexionPackage

method2class = {
    "vanilla": MAS,
    "cot": CoT,
    "self_consistency": SelfConsistency,
    "self_consistency_package": SelfConsistency_package,
    # "llm_debate_math": LLMDebate_MATH,
    # "llm_debate_gsm": LLMDebate_GSM,
    # "llm_debate_mmlu": LLMDebate_MMLU,
    "llm_debate_package": LLMDebate_package,
    "llm_debate": LLMDebate,
    # "chatdev_srdd": ChatDev_SRDD,
    "autogen": AutoGen,
    "mapcoder_humaneval": MapCoder_HumanEval,
    "mapcoder_mbpp": MapCoder_MBPP,
    "mapcoder_package": MapCoder_Package,
    # "dylan":DyLAN_Main,
    # "dylan_mmlu":DyLAN_MMLU,
    # "dylan_humaneval":DyLAN_Humaneval,
    # "dylan_math":DyLAN_MATH,
    # "medagents": MedAgents,
    # "agentverse_humaneval": Agentverse_HumanEval,
    # "agentverse_mgsm": Agentverse_MGSM,
    # "agentverse": Agentverse_MAIN,
    "agentverse_package": Agentverse_Package1,
    # "evomac": EvoMAC,
    # "macnet": Macnet,
    # "macnet_srdd": Macnet_SRDD,
    "mad": MAD,
    "mad_package": MAD_Package,
    "metagpt": MetaGPT,
    "metagpt_package": MetaGPT_Package,
    # "mav": MAV,
    # "mav_math": MAV_MATH,
    # "mav_humaneval": MAV_HumanEval,
    # "mav_gpqa": MAV_GPQA,
    # "mav_mmlu": MAV_MMLU
    "self_refine": SelfRefinePackage,
    "reflexion": ReflexionPackage
}

def get_method_class(method_name, dataset_name=None):
    
    # lowercase the method name
    method_name = method_name.lower()
    
    all_method_names = method2class.keys()
    matched_method_names = [sample_method_name for sample_method_name in all_method_names if method_name in sample_method_name]
    
    if len(matched_method_names) > 0:
        if dataset_name is not None:
            # lowercase the dataset name
            dataset_name = dataset_name.lower()
            # check if there are method names that contain the dataset name
            matched_method_data_names = [sample_method_name for sample_method_name in matched_method_names if sample_method_name.split('_')[-1] in dataset_name]
            if len(matched_method_data_names) > 0:
                method_name = matched_method_data_names[0]
                if len(matched_method_data_names) > 1:
                    print(f"[WARNING] Found multiple methods matching {dataset_name}: {matched_method_data_names}. Using {method_name} instead.")
    else:
        raise ValueError(f"[ERROR] No method found matching {method_name}. Please check the method name.")
    
    return method2class[method_name]