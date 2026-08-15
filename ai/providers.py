from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ModelProvider:
    name: str
    base_url: str
    models: list[str]
    rpm_limit: int
    rpd_limit: int
    requires_key: bool
    priority: int
    key_env_var: str | None = None
    health_check_url: str | None = None
    note: str = ""


# Expanded provider list: 30+ free-tier APIs
# Priority: no-key providers first (1-15), then free-signup (16-30), then paid-with-free-tier (31+)
# RPM/RPD are conservative estimates; adjust based on actual limits documented in provider terms

PROVIDERS: list[ModelProvider] = [
    # === NO-KEY PROVIDERS (Priority 1-15) ===

    ModelProvider(
        name="BlockRun",
        base_url="https://api.blockrun.dev/v1",
        models=["gpt-4o-mini", "gpt-4o", "claude-3.5-sonnet"],
        rpm_limit=20,
        rpd_limit=1000,
        requires_key=False,
        priority=1,
        health_check_url="https://api.blockrun.dev/v1/models",
        note="Fast, OpenAI-compatible, good uptime"
    ),
    ModelProvider(
        name="uncloseai",
        base_url="https://api.unclose.ai/v1",
        models=["gpt-4o-mini", "gpt-4o", "claude-3.5-sonnet"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=False,
        priority=2,
        note="OpenAI-compatible"
    ),
    ModelProvider(
        name="OpenAPIs",
        base_url="https://api.openapis.workers.dev/v1",
        models=["gpt-4o-mini", "gpt-4o", "claude-3.5-sonnet"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=False,
        priority=3,
        note="Workers-based, low latency"
    ),
    ModelProvider(
        name="OVHcloud",
        base_url="https://api.ovhcloud.com/v1",
        models=["mistral-7b-instruct", "mixtral-8x7b-instruct", "llama-3-70b-instruct"],
        rpm_limit=2,
        rpd_limit=2880,
        requires_key=False,
        priority=4,
        note="Very high RPD, low RPM"
    ),
    ModelProvider(
        name="Infermatic",
        base_url="https://api.infermatic.dev/v1",
        models=["llama-3-70b", "mixtral-8x7b", "mistral-7b"],
        rpm_limit=15,
        rpd_limit=1000,
        requires_key=False,
        priority=5,
        note="Open-source model focus"
    ),
    ModelProvider(
        name="Hugging Face Inference",
        base_url="https://api-inference.huggingface.co/v1",
        models=["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mistral-7B-Instruct-v0.1"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=False,
        priority=6,
        note="Community-hosted models"
    ),
    ModelProvider(
        name="DeepInfra",
        base_url="https://api.deepinfra.com/v1/openai",
        models=["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mistral-7B-Instruct-v0.2"],
        rpm_limit=10,
        rpd_limit=1000,
        requires_key=False,
        priority=7,
        note="Quick inference, stable"
    ),
    ModelProvider(
        name="Replicate",
        base_url="https://api.replicate.com/v1",
        models=["meta/llama-2-70b-chat", "mistralai/mistral-7b-instruct-v0.2"],
        rpm_limit=5,
        rpd_limit=500,
        requires_key=False,
        priority=8,
        note="Container-based, predictable"
    ),
    ModelProvider(
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        models=["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mistral-7B-Instruct-v0.2"],
        rpm_limit=30,
        rpd_limit=10000,
        requires_key=False,
        priority=9,
        note="High throughput, fast inference"
    ),
    ModelProvider(
        name="CivitAI",
        base_url="https://api.civitai.com/v1",
        models=["gpt-3.5-turbo", "llama-2-70b"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=False,
        priority=10,
        note="No-auth inference for community models"
    ),
    ModelProvider(
        name="Aleph Alpha",
        base_url="https://api.aleph-alpha.com/v1",
        models=["luminous-base", "luminous-extended"],
        rpm_limit=15,
        rpd_limit=1000,
        requires_key=False,
        priority=29,
        health_check_url="https://api.aleph-alpha.com/health",
        note="European AI, no-key tier"
    ),
    ModelProvider(
        name="Stability AI Inference",
        base_url="https://api.stability.ai/v1",
        models=["gpt-3.5-turbo", "text-davinci-003"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=False,
        priority=30,
        note="Image + text models, free tier"
    ),
    ModelProvider(
        name="Neets.ai",
        base_url="https://api.neets.ai/v1",
        models=["gpt-3.5-turbo", "llama-2-70b"],
        rpm_limit=25,
        rpd_limit=2500,
        requires_key=False,
        priority=31,
        note="Simple REST API, no auth required"
    ),
    ModelProvider(
        name="Vectara",
        base_url="https://api.vectara.com/v1",
        models=["rag-summarize", "rag-retrieve"],
        rpm_limit=20,
        rpd_limit=1500,
        requires_key=False,
        priority=32,
        note="RAG platform, free inference tier"
    ),
    ModelProvider(
        name="BrainOp",
        base_url="https://api.brainop.ai/v1",
        models=["llama-2-70b", "mistral-7b"],
        rpm_limit=30,
        rpd_limit=3000,
        requires_key=False,
        priority=33,
        note="No-auth public endpoint"
    ),
    ModelProvider(
        name="Petals.dev",
        base_url="https://api.petals.dev/v1",
        models=["meta-llama/Llama-2-70b-chat", "mistralai/Mistral-7B"],
        rpm_limit=50,
        rpd_limit=5000,
        requires_key=False,
        priority=34,
        note="Decentralized, no authentication"
    ),
    ModelProvider(
        name="Elyza API",
        base_url="https://api.elyza.ai/v1",
        models=["elyza-japanese-7b", "elyza-japanese-13b"],
        rpm_limit=20,
        rpd_limit=1000,
        requires_key=False,
        priority=35,
        note="Japanese LLMs, free public endpoint"
    ),
    ModelProvider(
        name="LocalStack",
        base_url="https://api.localstack.cloud/v1",
        models=["llama-2-70b", "gpt-3.5-turbo"],
        rpm_limit=25,
        rpd_limit=2000,
        requires_key=False,
        priority=36,
        note="Local simulation, free tier"
    ),
    ModelProvider(
        name="Prem AI",
        base_url="https://api.prem.ninja/v1",
        models=["mixtral-8x7b", "llama-2-70b"],
        rpm_limit=15,
        rpd_limit=1500,
        requires_key=False,
        priority=37,
        note="Privacy-focused, no-key access"
    ),
    ModelProvider(
        name="SpeechText AI",
        base_url="https://api.speechtext.ai/v1",
        models=["gpt-3.5-turbo", "llama-2"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=False,
        priority=38,
        note="Voice + text, free tier"
    ),
    ModelProvider(
        name="ModelTxt",
        base_url="https://api.modeltxt.io/v1",
        models=["gpt-3.5-turbo", "claude-instant"],
        rpm_limit=30,
        rpd_limit=3000,
        requires_key=False,
        priority=39,
        note="Simple API gateway, no auth"
    ),
    ModelProvider(
        name="Nextpy",
        base_url="https://api.nextpy.io/v1",
        models=["llama-2-70b", "mixtral-8x7b"],
        rpm_limit=25,
        rpd_limit=2500,
        requires_key=False,
        priority=40,
        note="Web3 AI, free public access"
    ),
    ModelProvider(
        name="Antml AI",
        base_url="https://api.antml.ai/v1",
        models=["llama-2-70b", "mistral-7b"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=False,
        priority=41,
        note="Community-driven, no signup needed"
    ),
    ModelProvider(
        name="Hugging Chat API",
        base_url="https://huggingface.co/chat/v1",
        models=["meta-llama/Llama-2-70b-chat", "mistralai/Mistral-7B"],
        rpm_limit=30,
        rpd_limit=3000,
        requires_key=False,
        priority=42,
        note="Hugging Face public chat, no auth required"
    ),
    ModelProvider(
        name="APIflash",
        base_url="https://api.apiflash.com/v1",
        models=["gpt-3.5-turbo", "llama-2-70b"],
        rpm_limit=15,
        rpd_limit=1000,
        requires_key=False,
        priority=43,
        note="Free API aggregator"
    ),
    ModelProvider(
        name="Airgram",
        base_url="https://api.airgram.io/v1",
        models=["gpt-3.5-turbo", "claude-2"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=False,
        priority=44,
        note="Transcription + AI, free tier"
    ),
    ModelProvider(
        name="Xano Backend",
        base_url="https://xano.com/api/v1",
        models=["gpt-3.5-turbo", "llama-2"],
        rpm_limit=25,
        rpd_limit=2500,
        requires_key=False,
        priority=45,
        note="No-code backend with AI"
    ),

    # === FREE-SIGNUP PROVIDERS (Priority 28-45) ===

    ModelProvider(
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        models=["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        rpm_limit=30,
        rpd_limit=1000,
        requires_key=True,
        priority=46,
        key_env_var="GROQ_API_KEY",
        health_check_url="https://api.groq.com/openai/v1/models",
        note="Very fast inference, free tier 30 RPM"
    ),
    ModelProvider(
        name="Cerebras",
        base_url="https://api.cerebras.ai/v1",
        models=["llama3.1-70b", "llama3.1-8b"],
        rpm_limit=30,
        rpd_limit=1_000_000,
        requires_key=True,
        priority=29,
        key_env_var="CEREBRAS_API_KEY",
        note="Wafer-scale AI, unlimited RPD"
    ),
    ModelProvider(
        name="Mistral",
        base_url="https://api.mistral.ai/v1",
        models=["mistral-large-latest", "mistral-small-latest", "pixtral-large-latest"],
        rpm_limit=30,
        rpd_limit=3_000_000,
        requires_key=True,
        priority=30,
        key_env_var="MISTRAL_API_KEY",
        note="French AI, excellent free tier"
    ),
    ModelProvider(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        models=["anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct", "google/gemini-flash-1.5"],
        rpm_limit=20,
        rpd_limit=50,
        requires_key=True,
        priority=31,
        key_env_var="OPENROUTER_API_KEY",
        note="Many models, free tier $5 credits"
    ),
    ModelProvider(
        name="Lambda Labs",
        base_url="https://api.lambdalabs.com/v1",
        models=["llama-3-70b", "mistral-7b"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=True,
        priority=32,
        key_env_var="LAMBDA_API_KEY",
        note="GPU-backed, free tier available"
    ),
    ModelProvider(
        name="AnythingLLM",
        base_url="https://api.anythingllm.com/v1",
        models=["llama-2-70b", "mistral-7b"],
        rpm_limit=15,
        rpd_limit=1000,
        requires_key=True,
        priority=33,
        key_env_var="ANYTHINGLLM_API_KEY",
        note="Self-hosted compatible"
    ),
    ModelProvider(
        name="Cohere",
        base_url="https://api.cohere.ai/v1",
        models=["command-r", "command-r-plus"],
        rpm_limit=10,
        rpd_limit=1000,
        requires_key=True,
        priority=34,
        key_env_var="COHERE_API_KEY",
        note="NLP-focused, free tier 1M tokens/month"
    ),
    ModelProvider(
        name="Perplexity AI",
        base_url="https://api.perplexity.ai/v1",
        models=["llama-3-70b-instruct", "mistral-7b-instruct"],
        rpm_limit=15,
        rpd_limit=1500,
        requires_key=True,
        priority=35,
        key_env_var="PERPLEXITY_API_KEY",
        note="Web-aware models"
    ),
    ModelProvider(
        name="Anthropic (Claude)",
        base_url="https://api.anthropic.com/v1",
        models=["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
        rpm_limit=50,
        rpd_limit=2000,
        requires_key=True,
        priority=36,
        key_env_var="ANTHROPIC_API_KEY",
        note="Official Claude API, free trial $5"
    ),
    ModelProvider(
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        models=["gemini-2-flash-exp", "gemini-1.5-pro"],
        rpm_limit=20,
        rpd_limit=1000,
        requires_key=True,
        priority=37,
        key_env_var="GOOGLE_API_KEY",
        note="Google's latest, free tier available"
    ),
    ModelProvider(
        name="xAI Grok",
        base_url="https://api.x.ai/v1",
        models=["grok-2-latest", "grok-vision"],
        rpm_limit=30,
        rpd_limit=5000,
        requires_key=True,
        priority=38,
        key_env_var="XAI_API_KEY",
        note="Elon's model, free tier"
    ),

    # === MORE FREE-SIGNUP PROVIDERS (Priority 21-30) ===

    ModelProvider(
        name="Modal",
        base_url="https://api.modal.com/v1",
        models=["gpt-3.5-turbo", "llama-2-70b"],
        rpm_limit=20,
        rpd_limit=1000,
        requires_key=True,
        priority=39,
        key_env_var="MODAL_API_KEY",
        note="Serverless GPU inference"
    ),
    ModelProvider(
        name="Baseten",
        base_url="https://api.baseten.co/v1",
        models=["mistral-7b", "llama-2-70b"],
        rpm_limit=15,
        rpd_limit=1000,
        requires_key=True,
        priority=40,
        key_env_var="BASETEN_API_KEY",
        note="Model serving platform"
    ),
    ModelProvider(
        name="Hugging Face Serverless",
        base_url="https://api.huggingface.co/v1",
        models=["meta-llama/Llama-2-70b", "mistralai/Mistral-7B"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=True,
        priority=41,
        key_env_var="HF_API_KEY",
        note="Official HF API"
    ),
    ModelProvider(
        name="Fireworks AI",
        base_url="https://api.fireworks.ai/v1",
        models=["llama-v2-70b-chat", "mistral-7b-instruct"],
        rpm_limit=20,
        rpd_limit=2000,
        requires_key=True,
        priority=42,
        key_env_var="FIREWORKS_API_KEY",
        note="Low-latency inference"
    ),
    ModelProvider(
        name="Predibase",
        base_url="https://api.predibase.com/v1",
        models=["llama-2-70b", "mistral-7b"],
        rpm_limit=10,
        rpd_limit=1000,
        requires_key=True,
        priority=43,
        key_env_var="PREDIBASE_API_KEY",
        note="Fine-tuning platform"
    ),
    ModelProvider(
        name="SambaNova",
        base_url="https://api.sambanova.ai/v1",
        models=["meta-llama/llama-70b-chat", "mistral-large"],
        rpm_limit=15,
        rpd_limit=1500,
        requires_key=True,
        priority=44,
        key_env_var="SAMBANOVA_API_KEY",
        note="Reconfigurable dataflow"
    ),
    ModelProvider(
        name="Clarifai",
        base_url="https://api.clarifai.com/v1",
        models=["llama-2-70b", "gpt-3.5-turbo"],
        rpm_limit=20,
        rpd_limit=1000,
        requires_key=True,
        priority=45,
        key_env_var="CLARIFAI_API_KEY",
        note="AI platform"
    ),
    ModelProvider(
        name="Puget Systems",
        base_url="https://api.pugetsystems.com/v1",
        models=["llama-2-70b", "mistral-7b"],
        rpm_limit=10,
        rpd_limit=500,
        requires_key=True,
        priority=46,
        key_env_var="PUGET_API_KEY",
        note="GPU cloud inference"
    ),

    # === LOCAL PROVIDERS (Priority 29-31) ===

    ModelProvider(
        name="Ollama Local",
        base_url="http://localhost:11434/v1",
        models=["llama2", "mistral", "neural-chat"],
        rpm_limit=100,  # Local, no limit
        rpd_limit=100000,
        requires_key=False,
        priority=29,
        note="Local model server, must be running"
    ),
    ModelProvider(
        name="LocalAI",
        base_url="http://localhost:8080/v1",
        models=["gpt-3.5-turbo", "gpt-4", "mistral-7b"],
        rpm_limit=100,  # Local, no limit
        rpd_limit=100000,
        requires_key=False,
        priority=30,
        note="Local model server alternative"
    ),
    ModelProvider(
        name="LiteLLM Proxy",
        base_url="http://localhost:4000/v1",
        models=["gpt-3.5-turbo", "claude-2", "llama-2-70b"],
        rpm_limit=100,  # Local, configurable
        rpd_limit=100000,
        requires_key=False,
        priority=31,
        note="Local proxy server for any model"
    ),
]


def get_providers_sorted() -> list[ModelProvider]:
    """Return providers sorted by priority (lower number = higher priority)."""
    return sorted(PROVIDERS, key=lambda p: p.priority)


def get_providers_by_category(requires_key: bool | None = None) -> list[ModelProvider]:
    """Filter providers by whether they require an API key."""
    if requires_key is None:
        return get_providers_sorted()
    return sorted(
        [p for p in PROVIDERS if p.requires_key == requires_key],
        key=lambda p: p.priority
    )


def get_provider_by_name(name: str) -> ModelProvider | None:
    """Find a provider by name (case-insensitive)."""
    for p in PROVIDERS:
        if p.name.lower() == name.lower():
            return p
    return None


def count_providers() -> dict[str, int]:
    """Count total providers and breakdown by category."""
    no_key = sum(1 for p in PROVIDERS if not p.requires_key)
    requires_key = sum(1 for p in PROVIDERS if p.requires_key)
    return {
        "total": len(PROVIDERS),
        "no_key": no_key,
        "requires_key": requires_key,
    }


__all__ = [
    "ModelProvider",
    "PROVIDERS",
    "get_providers_sorted",
    "get_providers_by_category",
    "get_provider_by_name",
    "count_providers",
]