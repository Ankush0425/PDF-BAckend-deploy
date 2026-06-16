"""
Document Analysis — AI-powered Resume, Invoice, Contract, and Research Paper analysis.
"""

from pathlib import Path

from core.ai_features import _call_ai, _prepare_text
from utils.logger import get_logger

logger = get_logger("document_analysis")


def analyze_resume(pdf_path: Path, backend: str = "ollama",
                   api_key: str = "", model: str = "") -> str:
    """
    Analyze a resume/CV and extract structured information.

    Returns formatted analysis with skills, experience, education, and suggestions.
    """
    text = _prepare_text(pdf_path)
    system_prompt = "You are an expert HR recruiter and resume analyst."
    prompt = (
        "Analyze this resume/CV and provide a comprehensive report:\n\n"
        "1. **Contact Information**: Name, email, phone, location\n"
        "2. **Professional Summary**: Brief overview of the candidate\n"
        "3. **Skills Extraction**:\n"
        "   - Technical Skills\n"
        "   - Soft Skills\n"
        "   - Tools & Technologies\n"
        "4. **Experience Summary**: Each role with key achievements\n"
        "5. **Education**: Degrees, institutions, dates\n"
        "6. **Certifications & Awards**\n"
        "7. **Strengths**: Top 3 strengths of this candidate\n"
        "8. **Areas for Improvement**: Suggestions to enhance the resume\n"
        "9. **Overall Score**: Rate out of 10 with justification\n"
        "10. **Recommended Job Titles**: Based on their profile\n\n"
        f"RESUME:\n{text}"
    )
    result = _call_ai(prompt, system_prompt, backend, api_key, model)
    logger.info("Resume analysis completed")
    return result


def analyze_invoice(pdf_path: Path, backend: str = "ollama",
                    api_key: str = "", model: str = "") -> str:
    """
    Analyze an invoice and extract structured data.

    Returns formatted analysis with line items, totals, vendor info, dates.
    """
    text = _prepare_text(pdf_path)
    system_prompt = "You are an expert accountant and invoice analyzer."
    prompt = (
        "Analyze this invoice and extract all relevant information:\n\n"
        "1. **Invoice Details**:\n"
        "   - Invoice Number\n"
        "   - Invoice Date\n"
        "   - Due Date\n"
        "   - Payment Terms\n"
        "2. **Vendor Information**: Name, address, contact\n"
        "3. **Customer Information**: Name, address, contact\n"
        "4. **Line Items**: (as a table)\n"
        "   - Description | Quantity | Unit Price | Amount\n"
        "5. **Financial Summary**:\n"
        "   - Subtotal\n"
        "   - Tax (rate and amount)\n"
        "   - Discounts\n"
        "   - Total Amount Due\n"
        "6. **Payment Information**: Bank details, payment methods\n"
        "7. **Notes/Terms**: Any additional terms or notes\n\n"
        f"INVOICE:\n{text}"
    )
    result = _call_ai(prompt, system_prompt, backend, api_key, model)
    logger.info("Invoice analysis completed")
    return result


def analyze_contract(pdf_path: Path, backend: str = "ollama",
                     api_key: str = "", model: str = "") -> str:
    """
    Analyze a contract/legal document.

    Returns analysis of key clauses, obligations, risks, and important dates.
    """
    text = _prepare_text(pdf_path)
    system_prompt = "You are an expert legal analyst specializing in contract review."
    prompt = (
        "Analyze this contract and provide a comprehensive review:\n\n"
        "1. **Contract Overview**:\n"
        "   - Type of Agreement\n"
        "   - Parties Involved\n"
        "   - Effective Date & Duration\n"
        "2. **Key Clauses**: Summarize each major clause\n"
        "3. **Obligations**:\n"
        "   - Party A's obligations\n"
        "   - Party B's obligations\n"
        "4. **Financial Terms**: Payment terms, amounts, penalties\n"
        "5. **Termination Conditions**: How can the contract be ended?\n"
        "6. **Risk Assessment**:\n"
        "   - Potential risks for each party\n"
        "   - Unfavorable clauses\n"
        "   - Missing protections\n"
        "7. **Important Dates**: All deadlines and milestones\n"
        "8. **Recommendations**: Key points to negotiate or be aware of\n\n"
        "⚠️ Note: This is an AI analysis and not legal advice.\n\n"
        f"CONTRACT:\n{text}"
    )
    result = _call_ai(prompt, system_prompt, backend, api_key, model)
    logger.info("Contract analysis completed")
    return result


def analyze_research_paper(pdf_path: Path, backend: str = "ollama",
                           api_key: str = "", model: str = "") -> str:
    """
    Analyze a research paper and provide a structured summary.

    Returns analysis covering abstract, methodology, findings, and limitations.
    """
    text = _prepare_text(pdf_path)
    system_prompt = "You are an expert academic researcher and paper reviewer."
    prompt = (
        "Analyze this research paper and provide a structured review:\n\n"
        "1. **Paper Overview**:\n"
        "   - Title\n"
        "   - Authors\n"
        "   - Publication/Journal\n"
        "   - Year\n"
        "2. **Abstract Summary**: What is this paper about?\n"
        "3. **Research Question/Hypothesis**: What problem does it address?\n"
        "4. **Methodology**:\n"
        "   - Research design\n"
        "   - Data collection methods\n"
        "   - Sample size/scope\n"
        "5. **Key Findings**: Main results and discoveries\n"
        "6. **Data & Statistics**: Important numbers and metrics\n"
        "7. **Discussion**: Authors' interpretation of results\n"
        "8. **Limitations**: Acknowledged and observed limitations\n"
        "9. **Conclusions**: Main takeaways\n"
        "10. **Future Work**: Suggested areas for further research\n"
        "11. **Quality Assessment**: Rate the paper's methodology and rigor\n\n"
        f"PAPER:\n{text}"
    )
    result = _call_ai(prompt, system_prompt, backend, api_key, model)
    logger.info("Research paper analysis completed")
    return result
