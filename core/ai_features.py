import os
from pathlib import Path

from config import (
    OPENAI_DEFAULT_MODEL, OLLAMA_DEFAULT_MODEL, OLLAMA_BASE_URL,
    GROQ_DEFAULT_MODEL, GROQ_DEFAULT_API_KEY,
    AI_MAX_CONTEXT_LENGTH, AI_CHUNK_SIZE, AI_CHUNK_OVERLAP,
)
from utils.helpers import extract_text_from_pdf
from utils.logger import get_logger

logger = get_logger("ai_features")


# ──────────────────────────────────────────────
# Security & Safety Guardrails
# ──────────────────────────────────────────────
def validate_prompt(prompt: str) -> None:
    """Guardrail to filter dangerous/malicious query keywords or prompt injection attempts."""
    block_words = [
        "system override", "ignore previous instructions", "bypass restriction", 
        "ignore rules", "write exploit", "generate malware", "ignore safety guidelines"
    ]
    p_lower = prompt.lower()
    for word in block_words:
        if word in p_lower:
            raise ValueError(f"Security Guardrail: Input query contains restricted phrase: '{word}'")


def validate_pdf_content(text: str) -> None:
    """Guardrail to verify that PDF has extracted text to analyze."""
    if not text or not text.strip():
        raise ValueError("Content Guardrail: The uploaded PDF does not contain extractable text (it might be scanned, try OCR first).")


# ──────────────────────────────────────────────
# AI Backend Abstraction
# ──────────────────────────────────────────────
def _call_openai(prompt: str, system_prompt: str = "", api_key: str = "",
                 model: str = OPENAI_DEFAULT_MODEL) -> str:
    """Call OpenAI API."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(model=model, messages=messages,
                                                    temperature=0.7, max_tokens=4096)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        raise RuntimeError(f"OpenAI API error: {e}") from e


def _call_groq(prompt: str, system_prompt: str = "", api_key: str = "",
               model: str = GROQ_DEFAULT_MODEL) -> str:
    """Call Groq API."""
    try:
        from openai import OpenAI
        key = api_key or os.environ.get("GROQ_API_KEY") or GROQ_DEFAULT_API_KEY
        
        client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1"
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model or GROQ_DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq call failed: {e}")
        raise RuntimeError(f"Groq API error: {e}") from e


def _call_ollama(prompt: str, system_prompt: str = "",
                 model: str = OLLAMA_DEFAULT_MODEL) -> str:
    """Call Ollama local model."""
    try:
        import ollama
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise RuntimeError(f"Ollama error: {e}") from e


def _call_ai(prompt: str, system_prompt: str = "", backend: str = "groq",
             api_key: str = "", model: str = "") -> str:
    """Unified AI call dispatcher."""
    # Guardrail check on prompt
    validate_prompt(prompt)

    if backend == "openai":
        m = model or OPENAI_DEFAULT_MODEL
        return _call_openai(prompt, system_prompt, api_key, m)
    elif backend == "groq":
        m = model or GROQ_DEFAULT_MODEL
        return _call_groq(prompt, system_prompt, api_key, m)
    else:
        m = model or OLLAMA_DEFAULT_MODEL
        return _call_ollama(prompt, system_prompt, m)


def _ensure_ollama_running() -> None:
    """Auto-start the bundled local Ollama server if it is not already running."""
    import subprocess, time
    try:
        from config import LOCAL_OLLAMA, LOCAL_OLLAMA_MODELS
        if not LOCAL_OLLAMA.exists():
            return
        # Quick ping — if OK, nothing to do
        import httpx
        try:
            httpx.head("http://localhost:11434", timeout=1.0)
            return
        except Exception:
            pass
        # Start the bundled server in the background
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(LOCAL_OLLAMA_MODELS)
        subprocess.Popen(
            [str(LOCAL_OLLAMA), "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logger.info("Auto-started local Ollama server")
        time.sleep(3)  # Give it a moment to initialise
    except Exception as e:
        logger.warning(f"Could not auto-start Ollama: {e}")


def check_ollama_available() -> bool:
    """Check if Ollama server is running (auto-starts local binary if needed)."""
    try:
        _ensure_ollama_running()
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def get_ollama_models() -> list[str]:
    """Get list of available Ollama models."""
    try:
        import ollama
        models = ollama.list()
        return [m.model for m in models.models] if models.models else []
    except Exception:
        return []


# ──────────────────────────────────────────────
# Text Preparation
# ──────────────────────────────────────────────
def _prepare_text(pdf_path: Path, max_length: int = AI_MAX_CONTEXT_LENGTH) -> str:
    """Extract and truncate text from PDF for AI processing."""
    text = extract_text_from_pdf(pdf_path)
    validate_pdf_content(text)  # Guardrail check on PDF content
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[... text truncated due to length ...]"
    return text


# ──────────────────────────────────────────────
# Chat with PDF
# ──────────────────────────────────────────────
def chat_with_pdf(pdf_path: Path, question: str, chat_history: list[dict] | None = None,
                  backend: str = "ollama", api_key: str = "", model: str = "") -> str:
    """
    Chat with a PDF document by asking questions about its content.

    Args:
        pdf_path: Path to the PDF file.
        question: User's question.
        chat_history: Previous conversation messages.
        backend: 'openai' or 'ollama'.
        api_key: OpenAI API key (if using OpenAI).
        model: Specific model name.

    Returns:
        AI response string.
    """
    text = _prepare_text(pdf_path)
    system_prompt = (
        "CRITICAL INSTRUCTION: You are a strict PDF-bound Q&A assistant. "
        "You are FORBIDDEN from answering any general knowledge questions, programming/coding queries, "
        "mathematical challenges, or general writing tasks that are not directly related to or contained "
        "within the provided DOCUMENT CONTENT.\n"
        "Do not write code, do not explain general concepts, and do not assist with anything outside the document.\n"
        "If the user's question cannot be answered using ONLY the provided DOCUMENT CONTENT, "
        "you MUST respond exactly with: 'I cannot answer this question because the information is not present in the uploaded document.'"
    )

    history_context = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Last 6 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"\n{role.upper()}: {content}"

    prompt = (
        f"DOCUMENT CONTENT:\n{text}\n\n"
        f"CRITICAL RULE: Base your response ONLY on the DOCUMENT CONTENT above. If the question is about general coding/programming (like Two Sum, sorting, etc.) or unrelated general knowledge, you MUST refuse to answer and state that the information is not in the document.\n\n"
    )
    if history_context:
        prompt += f"CONVERSATION HISTORY:{history_context}\n\n"
    prompt += f"USER QUESTION: {question}"

    return _call_ai(prompt, system_prompt, backend, api_key, model)


# ──────────────────────────────────────────────
# Summarize PDF
# ──────────────────────────────────────────────
def summarize_pdf(pdf_path: Path, style: str = "concise",
                  backend: str = "ollama", api_key: str = "", model: str = "") -> str:
    """Summarize a PDF document."""
    text = _prepare_text(pdf_path)
    system_prompt = "You are an expert document summarizer."

    style_instructions = {
        "concise": "Provide a concise summary in 3-5 paragraphs.",
        "detailed": "Provide a comprehensive, detailed summary covering all main points.",
        "bullet": "Provide the summary as organized bullet points.",
        "executive": "Provide an executive summary suitable for decision-makers.",
    }

    prompt = (f"Summarize the following document.\n"
              f"Style: {style_instructions.get(style, style_instructions['concise'])}\n\n"
              f"DOCUMENT:\n{text}")

    return _call_ai(prompt, system_prompt, backend, api_key, model)


# ──────────────────────────────────────────────
# Explain PDF
# ──────────────────────────────────────────────
def explain_pdf(pdf_path: Path, complexity: str = "simple",
                backend: str = "ollama", api_key: str = "", model: str = "") -> str:
    """Explain a PDF document in simple or detailed terms."""
    text = _prepare_text(pdf_path)

    complexity_map = {
        "simple": "Explain this as if to a 10-year-old. Use simple language.",
        "moderate": "Explain this for someone with basic knowledge of the topic.",
        "detailed": "Provide a thorough, technical explanation for an expert audience.",
    }

    prompt = (f"{complexity_map.get(complexity, complexity_map['simple'])}\n\n"
              f"DOCUMENT:\n{text}")

    return _call_ai(prompt, "You are a patient, clear teacher.", backend, api_key, model)


# ──────────────────────────────────────────────
# Generate Notes
# ──────────────────────────────────────────────
def generate_notes(pdf_path: Path, backend: str = "ollama",
                   api_key: str = "", model: str = "") -> str:
    """Generate structured study notes from a PDF."""
    text = _prepare_text(pdf_path)
    prompt = (
        "Create comprehensive, well-organized study notes from this document.\n"
        "Include:\n"
        "- Main topics and subtopics\n"
        "- Key definitions and concepts\n"
        "- Important facts and figures\n"
        "- Summary of each section\n"
        "Format with clear headings, bullet points, and highlights.\n\n"
        f"DOCUMENT:\n{text}"
    )
    return _call_ai(prompt, "You are an expert note-taker and study guide creator.",
                    backend, api_key, model)


# ──────────────────────────────────────────────
# Generate Interview Questions
# ──────────────────────────────────────────────
def generate_questions(pdf_path: Path, num_questions: int = 10,
                       difficulty: str = "mixed", backend: str = "ollama",
                       api_key: str = "", model: str = "") -> str:
    """Generate interview/study questions from a PDF."""
    text = _prepare_text(pdf_path)
    prompt = (
        f"Generate {num_questions} interview/study questions based on this document.\n"
        f"Difficulty level: {difficulty}\n"
        "Include a mix of:\n"
        "- Factual questions\n"
        "- Conceptual questions\n"
        "- Application-based questions\n"
        "- Critical thinking questions\n"
        "Provide the answer for each question.\n\n"
        f"DOCUMENT:\n{text}"
    )
    return _call_ai(prompt, "You are an expert interviewer and educator.",
                    backend, api_key, model)


# ──────────────────────────────────────────────
# Translate PDF Content
# ──────────────────────────────────────────────
def translate_pdf(pdf_path: Path, target_language: str = "Spanish",
                  backend: str = "ollama", api_key: str = "", model: str = "") -> str:
    """Translate PDF content to a target language."""
    text = _prepare_text(pdf_path)
    prompt = (
        f"Translate the following document content to {target_language}.\n"
        "Maintain the original formatting and structure as much as possible.\n\n"
        f"DOCUMENT:\n{text}"
    )
    return _call_ai(prompt, f"You are a professional translator. Translate to {target_language}.",
                    backend, api_key, model)


# ──────────────────────────────────────────────
# Extract Key Points
# ──────────────────────────────────────────────
def extract_key_points(pdf_path: Path, backend: str = "ollama",
                       api_key: str = "", model: str = "") -> str:
    """Extract key points and takeaways from a PDF."""
    text = _prepare_text(pdf_path)
    prompt = (
        "Extract the key points and main takeaways from this document.\n"
        "Present them as:\n"
        "1. A list of key points (numbered)\n"
        "2. Main arguments or findings\n"
        "3. Critical data or statistics mentioned\n"
        "4. Conclusions and recommendations\n\n"
        f"DOCUMENT:\n{text}"
    )
    return _call_ai(prompt, "You are an expert analyst.", backend, api_key, model)
