import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from src.config import get_nvidia_model_name

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = get_nvidia_model_name()
API_KEY = os.getenv("NVIDIA_API_KEY")

MAX_RETRIES = 3
INITIAL_WAIT = 5
TIMEOUT = 180


def generate_mitigation_strategy(ticket_details, risk_level, top_risk_factors):
    if not API_KEY:
        return {
            "reasoning_trace": "NVIDIA_API_KEY not found in .env file.",
            "final_strategy": "Unable to generate mitigation strategy. Add your NVIDIA API key to the .env file.",
        }

    prompt = (
        f"You are an Agile Project Management Expert. "
        f"A Jira ticket has been flagged as {risk_level} Risk. "
        f"The top SHAP drivers are: {top_risk_factors}. "
        f"The ticket details are: {ticket_details}. "
        f"You MUST format your exact response using these XML tags:\n"
        f"<reasoning>\n"
        f"[Your step-by-step analysis of the SHAP metrics]\n"
        f"</reasoning>\n"
        f"<strategy>\n"
        f"[Your concrete 3-step mitigation plan]\n"
        f"</strategy>"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    raw_content = ""
    wait_time = INITIAL_WAIT

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                NVIDIA_API_URL, json=payload, headers=headers, timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"].get("content", "")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < MAX_RETRIES:
                print(
                    f"[WARNING] NVIDIA API timed out. Retrying in {wait_time} seconds (Attempt {attempt}/{MAX_RETRIES})..."
                )
                time.sleep(wait_time)
                wait_time *= 2
            else:
                print(
                    f"[ERROR] NVIDIA API unresponsive after {MAX_RETRIES} attempts. Giving up."
                )
                return {
                    "reasoning_trace": "Error: NVIDIA API is currently unresponsive due to high server load.",
                    "final_strategy": "Please try generating the strategy again in a few minutes. Network connection timed out after multiple attempts.",
                }
        except requests.exceptions.RequestException as e:
            return {
                "reasoning_trace": f"NVIDIA API connection failed: {e}",
                "final_strategy": "Unable to generate mitigation strategy. Check your API key and internet connection.",
            }
        except (KeyError, IndexError) as e:
            return {
                "reasoning_trace": f"Unexpected API response format: {e}",
                "final_strategy": "Unable to parse mitigation strategy from API response.",
            }

    reasoning_trace = ""
    final_strategy = ""

    reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", raw_content, re.DOTALL)
    if reasoning_match:
        reasoning_trace = reasoning_match.group(1).strip()

    strategy_match = re.search(r"<strategy>(.*?)</strategy>", raw_content, re.DOTALL)
    if strategy_match:
        final_strategy = strategy_match.group(1).strip()

    if not reasoning_trace and not final_strategy:
        final_strategy = raw_content.strip()

    return {
        "reasoning_trace": reasoning_trace,
        "final_strategy": final_strategy,
    }
