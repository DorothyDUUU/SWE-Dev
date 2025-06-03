import os
import yaml
import contextlib
import signal
import traceback
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps

from ..mas_base import MAS


# ====================================================================
# IMPROVED TEXT EXTRACTION LOGIC
# ====================================================================
# This implementation is inspired by and follows the same approach as
# the self_refine_math.py module, adapting its code extraction logic
# to work with general text answers instead of mathematical solutions.
# ====================================================================

def extract_answer(text):
    """
    Extract the main answer from text response.
    
    Args:
        text (str): Text containing the answer.
        
    Returns:
        str: Extracted answer, or the original text if no clear pattern found.
    """
    # First try to extract content enclosed in triple backticks
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Get the first match and strip whitespace
        answer = matches[0].strip()
        return answer
    
    # Try to find answers with specific patterns
    answer_patterns = [
        r"(?:Answer|ANSWER|Final Answer):[\s\n]*(.*?)(?:\n\n|\Z)",
        r"(?:The answer is|My answer is|In conclusion):[\s\n]*(.*?)(?:\n\n|\Z)",
        r"(?:Therefore|Hence|Thus|So),[\s\n]*(.*?)(?:\n\n|\Z)"
    ]
    
    for pattern in answer_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If no patterns match, return the last paragraph as the answer
    paragraphs = text.split("\n\n")
    if paragraphs:
        return paragraphs[-1].strip()
    
    # If all else fails, return the original text
    return text.strip()


def extract_improved_answer(feedback_text):
    """
    Extract improved answer from feedback text.
    
    Args:
        feedback_text (str): Text containing feedback and improved answer.
        
    Returns:
        Tuple[str, str]: Extracted feedback and improved answer.
    """
    # Try to find the most common patterns where the improved answer starts
    improved_markers = [
        "Here is a corrected and more detailed answer:",
        "Here is the corrected and improved answer:",
        "Here's a refined version of the answer:",
        "Here is a refined version of the answer:",
        "Here's a refined version of the answer that addresses these points:",
        "Improved Answer:",
        "Here is the corrected answer:",
        "Here's the corrected answer:",
        "Here is my improved answer:",
    ]
    
    # Look for these markers to separate feedback from improved answer
    for marker in improved_markers:
        if marker in feedback_text:
            parts = feedback_text.split(marker, 1)
            if len(parts) == 2:
                feedback = parts[0].strip()
                improved_answer = parts[1].strip()
                return feedback, improved_answer
    
    # Check for a section starting with "To determine" or similar phrases
    # which often indicates the start of an improved answer
    start_phrases = [
        "To determine", "To calculate", "To find out", 
        "Here is", "Here's", "Let's", "We can",
        "The answer is"
    ]
    
    # Check for paragraphs that might start with these phrases
    paragraphs = feedback_text.split("\n\n")
    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if any(paragraph.startswith(phrase) for phrase in start_phrases) and i > 0:
            feedback = "\n\n".join(paragraphs[:i]).strip()
            improved_answer = "\n\n".join(paragraphs[i:]).strip()
            return feedback, improved_answer
    
    # Look for sections with "---" which often separate the explanation from the answer
    if "---" in feedback_text:
        parts = feedback_text.split("---")
        if len(parts) >= 3:  # Format is usually: explanation --- answer --- note
            feedback = parts[0].strip()
            improved_answer = "---\n\n" + parts[1].strip() + "\n\n---"
            return feedback, improved_answer
    
    # If all else fails, check if there's a clear critique followed by a solution
    # by identifying feedback points (often numbered) and then finding where the answer starts
    if re.search(r'\d+\.\s+\*\*', feedback_text):  # Numbered feedback points with bold formatting
        # Try to find where the improved answer might start after the feedback points
        match = re.search(r'\n\n(To\s+\w+|\w+\'s\s+|Here\s+)', feedback_text)
        if match:
            split_pos = match.start()
            feedback = feedback_text[:split_pos].strip()
            improved_answer = feedback_text[split_pos:].strip()
            return feedback, improved_answer
    
    # If we still can't find a clear division, look for sentences that might
    # indicate the start of a new answer after some critique
    lines = feedback_text.splitlines()
    for i, line in enumerate(lines):
        if i > 3 and (line.startswith("To ") or line.startswith("The ")):
            potential_answer_start = True
            # Check if this is likely the start of an answer rather than feedback
            for prev_line in lines[max(0, i-3):i]:
                if "incorrect" in prev_line.lower() or "improvement" in prev_line.lower():
                    potential_answer_start = False
                    break
            
            if potential_answer_start:
                feedback = "\n".join(lines[:i]).strip()
                improved_answer = "\n".join(lines[i:]).strip()
                return feedback, improved_answer
    
    # First try to extract code blocks as they likely contain the improved answer
    pattern = r"```(.*?)```"
    code_blocks = re.findall(pattern, feedback_text, re.DOTALL)
    
    # If code blocks found, use the last one as the improved answer
    if code_blocks:
        # Get the last code block as the answer
        improved_answer = code_blocks[-1].strip()
        
        # Extract feedback (remove all code blocks)
        feedback = re.sub(pattern, "", feedback_text, flags=re.DOTALL).strip()
        return feedback, improved_answer
    
    # If we can't clearly identify separate feedback and improved answer,
    # analyze text structure to make a best guess
    lines = feedback_text.splitlines()
    feedback_indicators = ['incorrect', 'improve', 'error', 'missing', 'lacks', 'problem']
    answer_indicators = ['therefore', 'thus', 'in conclusion', 'total', 'result', 'finally']
    
    # Find a potential split point based on these indicators
    split_index = None
    for i, line in enumerate(lines):
        if i > len(lines) // 2:  # Only check in the latter half of text
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in answer_indicators):
                split_index = i
                break
    
    if split_index:
        # Find where the actual answer might start (a few lines before the conclusion)
        for i in range(max(0, split_index-10), split_index):
            if lines[i].strip() and not any(ind in lines[i].lower() for ind in feedback_indicators):
                feedback = "\n".join(lines[:i]).strip()
                improved_answer = "\n".join(lines[i:]).strip()
                return feedback, improved_answer
    
    # If we still can't determine, return the entire text as the improved answer
    # This is a fallback that should rarely be needed with the improved checks
    return "", feedback_text


class SelfRefineMain(MAS):
    def __init__(self, general_config, method_config_name=None):
        super().__init__(general_config, method_config_name)
        
        # Load config file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "config", "self_refine_main.yaml")
        with open(config_path, "r") as f:
            self.method_config = yaml.safe_load(f)
        
        # Set hyperparameters
        self.max_attempts = self.method_config.get("max_attempts", 4)
        self.feedback_type = self.method_config.get("feedback_type", "rich")
        
        # Configuration for initial query
        self.question_prefix = ""  # No prefix needed for general questions
        self.answer_prefix = ""    # No prefix needed for general answers
        self.intra_example_sep = "\n"
        self.inter_example_sep = "\n\n"
        
        # Configuration for feedback
        self.feedback_question_prefix = "Question: "
        self.feedback_answer_prefix = "Initial Answer: "
        self.feedback_intra_example_sep = "\n\n"
        self.feedback_inter_example_sep = "\n\n### END ###\n\n"
        self.feedback_stop_token = "### END"
        
        # Instruction for feedback
        self.instruction = "Please analyze the answer above for any errors, omissions, or areas of improvement. Then provide a better, more accurate answer."
        
        # Load prompt templates from config
        self.init_prompt = self.method_config.get("init_prompt", "")
        self.feedback_prompt = self.method_config.get("feedback_prompt", "")
        
        # Log file path
        self.log_filepath = os.path.join(current_dir, "selfrefine_extraction_log.json")
        self.extraction_log = []
    
    def _make_init_query(self, question: str) -> str:
        """Construct initialization query"""
        question = question.strip()
        query = f"{self.init_prompt}{self.question_prefix}{question}{self.intra_example_sep}{self.answer_prefix}"
        return query
    
    def _make_feedback_query(self, question: str, answer: str) -> str:
        """Construct feedback query with both question and answer"""
        feedback_query = f"{self.feedback_prompt}{self.feedback_question_prefix}{question}{self.feedback_intra_example_sep}{self.feedback_answer_prefix}{answer}{self.feedback_intra_example_sep}{self.instruction}"
        return feedback_query
    
    def _update_feedback_prompt(self, question: str, answer: str, improved_answer: str, feedback: str):
        """Update feedback prompt with new example"""
        prefix = f"{self.feedback_question_prefix}{question}{self.feedback_intra_example_sep}{self.feedback_answer_prefix}{answer}{self.feedback_intra_example_sep}{self.instruction}"
        
        gen_ans = f"""

{feedback}

{improved_answer.rstrip()}{self.feedback_inter_example_sep}"""

        new_example = f"{prefix}{gen_ans}"
        self.feedback_prompt = f"{self.feedback_prompt}{new_example}"
    
    def _save_extraction_log(self):
        """Save content extraction process log to file"""
        try:
            with open(self.log_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.extraction_log, f, ensure_ascii=False, indent=2)
            print(f"Extraction log saved to: {self.log_filepath}")
        except Exception as e:
            print(f"Error saving extraction log: {str(e)}")
    
    def _check_answer_correctness(self, feedback: str) -> bool:
        """Check if answer is correct based on feedback"""
        positive_indicators = [
            "it is correct",
            "the answer is correct",
            "this is a good answer",
            "no errors found"
        ]
        
        for indicator in positive_indicators:
            if indicator.lower() in feedback.lower():
                return True
        return False
    
    def inference(self, query: str) -> str:
        """Process query and return result with iterative refinement implementation"""
        max_retries = 3
        retries = max_retries
        log = []
        self.extraction_log = []  # Reset extraction log
        
        while retries > 0:
            try:
                # Core implementation of iterative refinement
                n_attempts = 0
                log = []
                
                # Generate initial answer
                init_query = self._make_init_query(query)
                answer_response = self.call_llm(prompt=init_query)
                
                # Extract answer from response using our improved extraction logic
                answer = extract_answer(answer_response)
                
                # Log extraction results
                self.extraction_log.append({
                    "stage": "initial_answer",
                    "raw_response": answer_response,
                    "extracted_answer": answer
                })
                
                while n_attempts < self.max_attempts:
                    # Get feedback
                    feedback_query = self._make_feedback_query(query, answer)
                    feedback_response = self.call_llm(prompt=feedback_query)
                    
                    # Extract feedback and improved answer using our improved extraction logic
                    feedback, improved_answer = extract_improved_answer(feedback_response)
                    
                    # If we couldn't extract an improved answer, use the full response as the improved answer
                    if not improved_answer:
                        improved_answer = feedback_response
                        feedback = ""
                    
                    # Log extraction results
                    self.extraction_log.append({
                        "stage": f"feedback_attempt_{n_attempts}",
                        "raw_response": feedback_response,
                        "extracted_feedback": feedback,
                        "extracted_improved_answer": improved_answer
                    })
                    
                    # Record current iteration
                    log.append({
                        "attempt": n_attempts, 
                        "answer_curr": answer, 
                        "answer_improved": improved_answer, 
                        "feedback": feedback
                    })
                    
                    # Check if correct
                    if self._check_answer_correctness(feedback):
                        break
                    
                    # Update feedback prompt and current answer
                    self._update_feedback_prompt(query, answer, improved_answer, feedback)
                    answer = improved_answer
                    
                    n_attempts += 1
                
                # Successfully completed iteration process
                break
            except Exception as e:
                stack_trace = traceback.format_exc()
                retries -= 1
                print(f"An error occurred: {e}. {stack_trace}. Left retries: {retries}.")
        
        # Save content extraction log
        self._save_extraction_log()
        
        if not log:
            return "Could not generate answer"
        
        # Get final answer
        final_answer = log[-1]["answer_improved"]
        
        # Save iteration process log to JSON file
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_filepath = os.path.join(current_dir, "selfrefine_main_log.json")
            
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            
            print(f"Iteration log saved to: {log_filepath}")
        except Exception as e:
            print(f"Error saving iteration log: {str(e)}")
        
        # Return final result
        return final_answer