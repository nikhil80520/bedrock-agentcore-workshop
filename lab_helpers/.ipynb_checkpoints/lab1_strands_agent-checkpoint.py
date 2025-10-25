from strands.tools import tool
from ddgs.exceptions import DDGSException, RatelimitException
from ddgs import DDGS
from strands_tools import retrieve
import boto3

MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

SYSTEM_PROMPT = """You are a knowledgeable and reliable Tax Regulation Assistant specializing in U.S. federal and state tax laws.
Your role is to:
- Provide clear, accurate, and compliant information about tax codes, IRS publications, and state tax regulations.
- Help users understand tax policies, filing requirements, and regulatory updates.
- Be professional, neutral, and informative in all responses.
- When users ask about unclear or complex rules, refer them to the relevant official IRS or state documentation.
- Always clarify that your responses are for informational purposes only and do not constitute professional legal or financial advice.

You have access to the following tools:
1. get_tax_policy() - To retrieve IRS publications, Title 26 (Internal Revenue Code), and federal tax policies.
2. get_tax_code_info() - To access information on state-level tax regulations and compliance rules.
3. get_tax_detail() - For federal and state income tax bracket details by year from document.
4. web_search() - To access recent updates or official government resources related to taxation.

When answering, prioritize accuracy, cite the relevant tax authority or publication when possible, and maintain a professional and supportive tone.
"""

@tool
def web_search(keywords: str, region: str = "us-en", max_results: int = 5) -> str:
    """Search the web for updated information.

    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.

    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "Rate limit reached. Please try again later."
    except DDGSException as e:
        return f"Search error: {e}"
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def get_return_policy(product_category: str) -> str:
    """
    Get return policy information for a specific product category.

    Args:
        product_category: Electronics category (e.g., 'smartphones', 'laptops', 'accessories')

    Returns:
        Formatted return policy details including timeframes and conditions
    """
    # Mock return policy database - in real implementation, this would query policy database
    return_policies = {
        "smartphones": {
            "window": "30 days",
            "condition": "Original packaging, no physical damage, factory reset required",
            "process": "Online RMA portal or technical support",
            "refund_time": "5-7 business days after inspection",
            "shipping": "Free return shipping, prepaid label provided",
            "warranty": "1-year manufacturer warranty included",
        },
        "laptops": {
            "window": "30 days",
            "condition": "Original packaging, all accessories, no software modifications",
            "process": "Technical support verification required before return",
            "refund_time": "7-10 business days after inspection",
            "shipping": "Free return shipping with original packaging",
            "warranty": "1-year manufacturer warranty, extended options available",
        },
        "accessories": {
            "window": "30 days",
            "condition": "Unopened packaging preferred, all components included",
            "process": "Online return portal",
            "refund_time": "3-5 business days after receipt",
            "shipping": "Customer pays return shipping under $50",
            "warranty": "90-day manufacturer warranty",
        },
    }

    # Default policy for unlisted categories
    default_policy = {
        "window": "30 days",
        "condition": "Original condition with all included components",
        "process": "Contact technical support",
        "refund_time": "5-7 business days after inspection",
        "shipping": "Return shipping policies vary",
        "warranty": "Standard manufacturer warranty applies",
    }

    policy = return_policies.get(product_category.lower(), default_policy)
    return (
        f"Return Policy - {product_category.title()}:\n\n"
        f"• Return window: {policy['window']} from delivery\n"
        f"• Condition: {policy['condition']}\n"
        f"• Process: {policy['process']}\n"
        f"• Refund timeline: {policy['refund_time']}\n"
        f"• Shipping: {policy['shipping']}\n"
        f"• Warranty: {policy['warranty']}"
    )


@tool
def get_product_info(product_type: str) -> str:
    """
    Get detailed technical specifications and information for electronics products.

    Args:
        product_type: Electronics product type (e.g., 'laptops', 'smartphones', 'headphones', 'monitors')
    Returns:
        Formatted product information including warranty, features, and policies
    """
    # Mock product catalog - in real implementation, this would query a product database
    products = {
        "laptops": {
            "warranty": "1-year manufacturer warranty + optional extended coverage",
            "specs": "Intel/AMD processors, 8-32GB RAM, SSD storage, various display sizes",
            "features": "Backlit keyboards, USB-C/Thunderbolt, Wi-Fi 6, Bluetooth 5.0",
            "compatibility": "Windows 11, macOS, Linux support varies by model",
            "support": "Technical support and driver updates included",
        },
        "smartphones": {
            "warranty": "1-year manufacturer warranty",
            "specs": "5G/4G connectivity, 128GB-1TB storage, multiple camera systems",
            "features": "Wireless charging, water resistance, biometric security",
            "compatibility": "iOS/Android, carrier unlocked options available",
            "support": "Software updates and technical support included",
        },
        "headphones": {
            "warranty": "1-year manufacturer warranty",
            "specs": "Wired/wireless options, noise cancellation, 20Hz-20kHz frequency",
            "features": "Active noise cancellation, touch controls, voice assistant",
            "compatibility": "Bluetooth 5.0+, 3.5mm jack, USB-C charging",
            "support": "Firmware updates via companion app",
        },
        "monitors": {
            "warranty": "3-year manufacturer warranty",
            "specs": "4K/1440p/1080p resolutions, IPS/OLED panels, various sizes",
            "features": "HDR support, high refresh rates, adjustable stands",
            "compatibility": "HDMI, DisplayPort, USB-C inputs",
            "support": "Color calibration and technical support",
        },
    }
    product = products.get(product_type.lower())
    if not product:
        return f"Technical specifications for {product_type} not available. Please contact our technical support team for detailed product information and compatibility requirements."

    return (
        f"Technical Information - {product_type.title()}:\n\n"
        f"• Warranty: {product['warranty']}\n"
        f"• Specifications: {product['specs']}\n"
        f"• Key Features: {product['features']}\n"
        f"• Compatibility: {product['compatibility']}\n"
        f"• Support: {product['support']}"
    )


@tool
def get_technical_support(issue_description: str) -> str:
    try:
        # Get KB ID from parameter store
        ssm = boto3.client("ssm")
        account_id = boto3.client("sts").get_caller_identity()["Account"]
        region = boto3.Session().region_name

        kb_id = ssm.get_parameter(Name=f"/{account_id}-{region}/kb/knowledge-base-id")[
            "Parameter"
        ]["Value"]
        print(f"Successfully retrieved KB ID: {kb_id}")

        # Use strands retrieve tool
        tool_use = {
            "toolUseId": "tech_support_query",
            "input": {
                "text": issue_description,
                "knowledgeBaseId": kb_id,
                "region": region,
                "numberOfResults": 3,
                "score": 0.4,
            },
        }

        result = retrieve.retrieve(tool_use)

        if result["status"] == "success":
            return result["content"][0]["text"]
        else:
            return f"Unable to access technical support documentation. Error: {result['content'][0]['text']}"

    except Exception as e:
        print(f"Detailed error in get_technical_support: {str(e)}")
        return f"Unable to access technical support documentation. Error: {str(e)}"

from strands.models import BedrockModel
from strands import Agent
from strands_tools import retrieve
import boto3
from typing import Optional

@tool
def get_tax_information(query: str) -> str:
    """
    Retrieve relevant U.S. federal or state tax regulation information 
    from the knowledge base using the Strands retrieve tool.

    Args:
        query (str): User's tax-related question or topic (e.g., "capital gains tax rules", "IRS Publication 17").

    Returns:
        str: The most relevant tax regulation text or citation from the knowledge base.
    """
    try:
        # Initialize clients
        ssm = boto3.client("ssm")
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        region = boto3.Session().region_name

        # Retrieve Knowledge Base ID from AWS Parameter Store
        kb_param_name = f"/{account_id}-{region}/kb/knowledge-base-id"
        kb_id = ssm.get_parameter(Name=kb_param_name)["Parameter"]["Value"]
        print(f"✅ Retrieved Knowledge Base ID: {kb_id}")

        # Prepare retrieval request for tax documents
        tool_use = {
            "toolUseId": "tax_regulation_query",
            "input": {
                "text": query,
                "knowledgeBaseId": kb_id,
                "region": region,
                "numberOfResults": 3,
                "score": 0.4,
            },
        }

        result = retrieve.retrieve(tool_use)

        # Handle retrieval results
        if result.get("status") == "success" and result.get("content"):
            top_result = result["content"][0]["text"]
            return (
                f"📘 **Relevant Tax Regulation Information:**\n\n"
                f"{top_result}\n\n"
                f"*(Source: IRS Publications or U.S. Code Title 26. For official guidance, "
                f"refer to irs.gov or your state’s Department of Revenue.)*"
            )
        else:
            return (
                "⚠️ Unable to locate specific tax regulation details for your query. "
                "Please refine your question or consult the official IRS documentation at [irs.gov](https://www.irs.gov)."
            )

    except Exception as e:
        print(f"❌ Detailed error in get_tax_information: {str(e)}")
        return (
            f"An error occurred while retrieving tax regulation information: {str(e)}. "
            f"Please verify the knowledge base setup or try again later."
        )


print("✅ Tax information retrieval tool ready")
@tool
def get_tax_code_info(code_section: str) -> str:
    """
    Get detailed information and context for U.S. federal or state tax code sections or acts.

    Args:
        code_section: Tax section or act (e.g., 'Title 26', 'IRC Section 61', 'Bank Secrecy Act', 'OBBBA Regulations')

    Returns:
        Formatted tax code summary including authority, scope, key provisions, and compliance notes.
    """
    # Mock tax code catalog - in real implementation, this would query IRS, Treasury, or state law databases
    tax_codes = {
        "title 26": {
            "authority": "Internal Revenue Service (IRS)",
            "scope": "Comprehensive body of federal tax law, including income, estate, gift, and excise taxes.",
            "key_provisions": "Defines taxable income, deductions, credits, and enforcement procedures.",
            "references": "26 U.S.C. §§ 1–9834",
            "notes": "Often referred to as the Internal Revenue Code (IRC); foundation of U.S. tax law.",
        },
        "irc section 61": {
            "authority": "Internal Revenue Service (IRS)",
            "scope": "Defines 'gross income' as all income from whatever source derived.",
            "key_provisions": "Includes compensation, business income, rents, royalties, dividends, and interest.",
            "references": "26 U.S.C. § 61",
            "notes": "This section serves as the starting point for determining taxable income.",
        },
        "bank secrecy act": {
            "authority": "U.S. Department of the Treasury (FinCEN)",
            "scope": "Regulates financial reporting to detect and prevent money laundering and tax evasion.",
            "key_provisions": "Requires recordkeeping and reporting for cash transactions over $10,000.",
            "references": "31 U.S.C. §§ 5311–5330",
            "notes": "Important for tax compliance, especially for international and financial institutions.",
        },
        "obbba regulations": {
            "authority": "Office of the Comptroller of the Currency (OCC)",
            "scope": "Implements fair banking and consumer protection standards under tax-related financial oversight.",
            "key_provisions": "Covers compliance, disclosure, and regulatory standards for banks.",
            "references": "12 CFR Part 1000+",
            "notes": "Often cross-referenced in financial compliance audits and tax reporting reviews.",
        },
        "irs publication 55b": {
            "authority": "Internal Revenue Service (IRS)",
            "scope": "Provides guidance on employer filing requirements and electronic reporting systems.",
            "key_provisions": "Details rules for electronic filing, submission formats, and deadlines.",
            "references": "IRS Pub. 55-B",
            "notes": "Essential reference for businesses using IRS FIRE or e-file systems.",
        },
    }

    code_info = tax_codes.get(code_section.lower())
    if not code_info:
        return (
            f"Tax code information for '{code_section}' not found.\n"
            "Please refer to the IRS or state tax authority for official documentation."
        )

    return (
        f"📘 Tax Code Information - {code_section.title()}:\n\n"
        f"• Authority: {code_info['authority']}\n"
        f"• Scope: {code_info['scope']}\n"
        f"• Key Provisions: {code_info['key_provisions']}\n"
        f"• References: {code_info['references']}\n"
        f"• Notes: {code_info['notes']}"
    )


print("✅ get_tax_code_info tool ready")
@tool
def get_tax_policy(tax_category: str) -> str:
    """
    Get key tax policy information for a specific category.

    Args:
        tax_category: Tax category (e.g., 'income tax', 'corporate tax', 'sales tax', 'estate tax')

    Returns:
        Formatted overview of the selected tax policy, including filing deadlines, rates, and references.
    """
    # Mock tax policy database - in a real implementation, this would query IRS or state tax data sources
    tax_policies = {
        "income tax": {
            "authority": "Internal Revenue Service (IRS)",
            "code_reference": "Title 26, Subtitle A - Income Taxes",
            "filing_deadline": "April 15 (extensions available)",
            "rates": "Progressive rates ranging from 10% to 37% based on income brackets",
            "deductions": "Standard deduction and itemized deductions available",
            "note": "Taxpayers must report all income, including wages, interest, and dividends.",
        },
        "corporate tax": {
            "authority": "Internal Revenue Service (IRS)",
            "code_reference": "Title 26, Subtitle A, Chapter 1, Subchapter C",
            "filing_deadline": "April 15 for calendar-year corporations (extensions available)",
            "rates": "Flat 21% rate on taxable income",
            "deductions": "Business expenses, depreciation, and credits for R&D or foreign taxes",
            "note": "Corporations must file Form 1120 annually.",
        },
        "sales tax": {
            "authority": "State Revenue Departments",
            "code_reference": "Varies by state",
            "filing_deadline": "Monthly or quarterly depending on business volume",
            "rates": "Varies by state and locality (0%–10%)",
            "deductions": "Exemptions for groceries, medicine, or manufacturing equipment (state-specific)",
            "note": "Collected by sellers and remitted to state authorities.",
        },
        "estate tax": {
            "authority": "Internal Revenue Service (IRS)",
            "code_reference": "Title 26, Subtitle B, Chapter 11",
            "filing_deadline": "9 months after date of death (Form 706)",
            "rates": "Up to 40% above the federal exemption threshold ($13.61 million for 2024)",
            "deductions": "Charitable and marital deductions apply",
            "note": "Applies only to estates exceeding federal exemption thresholds.",
        },
    }

    # Default response for unknown category
    default_policy = {
        "authority": "IRS or state-level tax authority",
        "code_reference": "Refer to Title 26 or relevant state tax code",
        "filing_deadline": "Varies by jurisdiction and taxpayer type",
        "rates": "Progressive or flat depending on category",
        "deductions": "Standard and special deductions may apply",
        "note": "Consult the IRS or official state tax department for confirmation.",
    }

    policy = tax_policies.get(tax_category.lower(), default_policy)

    return (
        f"📘 Tax Policy Overview - {tax_category.title()}:\n\n"
        f"• Authority: {policy['authority']}\n"
        f"• Code Reference: {policy['code_reference']}\n"
        f"• Filing Deadline: {policy['filing_deadline']}\n"
        f"• Rates: {policy['rates']}\n"
        f"• Deductions: {policy['deductions']}\n"
        f"• Note: {policy['note']}"
    )


print("✅ Tax policy tool ready")
