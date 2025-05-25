from llama_index.core.llms import ChatMessage, MessageRole

from src.agents._signal import SignalEvent


def generate_output(llm, metrics: dict, prompt: str, name: str) -> SignalEvent:
    message = f"""
    You are in Stage 2 of your analytical process.
    Based on the provided financial data for a company, apply the "Decision Rules" you internalized in Stage 1 for each fundamental metric.
    Perform a comprehensive financial analysis.

    **Analysis Data:**
    {metrics}

    Generate your final assessment in the specified JSON format, ensuring the 'reasoning' field provides a detailed, markdown-style explanation for each metric's influence on the overall verdict, directly referencing its corresponding "Decision Rule."
    """

    chat = [
        ChatMessage.from_str(prompt, MessageRole.SYSTEM),
        ChatMessage.from_str(message, MessageRole.USER),
    ]

    response: SignalEvent = llm.chat(chat).raw
    response.agent = name
    return response
