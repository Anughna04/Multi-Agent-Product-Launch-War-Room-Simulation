import json
from typing import Dict, Any, List
from llm.llm_provider import LLMFactory
from utils.logger import logger
from utils.json_utils import extract_and_parse_json

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, tools: List[callable] = None, required_keys: List[str] = None):
        self.name = name
        if not system_prompt:
            raise ValueError(f"[{self.name}] system_prompt is mandatory and cannot be empty.")
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.required_keys = required_keys or []
        self.llm = LLMFactory.get_provider()
        
    def _execute_tools(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for tool in self.tools:
            tool_name = tool.__name__
            try:
                logger.info(f"[{self.name}] Executing tool: {tool_name}")
                safe_state = dict(state)  # copy state
                if "scenario" not in safe_state:
                    logger.error(f"[{self.name}] Scenario missing in state!")
                    safe_state["scenario"] = "scenario_1"  # fallback (safety)

                results[tool_name] = tool(safe_state)
            except Exception as e:
                logger.error(f"[{self.name}] Error executing {tool_name}: {e}")
                results[tool_name] = {"error": str(e)}
        return results

    def _validate_output(self, response_json: dict) -> None:
        missing_keys = [k for k in self.required_keys if k not in response_json]
        if missing_keys:
            raise KeyError(f"Missing required keys: {missing_keys}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Agent started processing.")
        logger.info(f"[{self.name}] Incoming state keys: {list(state.keys())}")
        logger.info(f"[{self.name}] Scenario in state: {state.get('scenario')}")
        
        # Determine tool results before LLM invocation
        tool_results = self._execute_tools(state)
        
        system_instruction = """
You MUST return ONLY valid JSON.
Do NOT include explanations, text, or markdown.
Do NOT include anything outside the JSON object.

You are given tool results below. Do NOT call tools.
Use ONLY the provided data.
"""

        prompt = f"""{self.system_prompt}

{system_instruction}

--------------------------------------------------
Current War Room State Context:
{json.dumps(state, indent=2, default=str)}

--------------------------------------------------
Tool Results:
{json.dumps(tool_results, indent=2, default=str)}

Return ONLY JSON. No extra text. Provide the EXACT output JSON structure defined in your prompt.
"""
        
        try:
            response = self.llm.generate(prompt)
            logger.debug(f"[DEBUG] Raw LLM output from {self.name}:\n{response}")
            
            response_json = extract_and_parse_json(response)
            self._validate_output(response_json)
            
            state[f"{self.name}_output"] = response_json
            logger.info(f"[{self.name}] Output generated successfully.")
        except Exception as e:
            logger.error(f"[{self.name}] Error during run: {e}")
            state[f"{self.name}_output"] = {"error": str(e), "failed": True}
            logger.error(f"[{self.name}] Agent failed abruptly.")
                
        return state
