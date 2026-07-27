import importlib
import inspect
from typing import Dict, Optional, Union

from memb.configs.embeddings.base import BaseEmbedderConfig
from memb.configs.llms.anthropic import AnthropicConfig
from memb.configs.llms.aws_bedrock import AWSBedrockConfig
from memb.configs.llms.azure import AzureOpenAIConfig
from memb.configs.llms.base import BaseLlmConfig
from memb.configs.llms.deepseek import DeepSeekConfig
from memb.configs.llms.gemini import GeminiConfig
from memb.configs.llms.lmstudio import LMStudioConfig
from memb.configs.llms.minimax import MinimaxConfig
from memb.configs.llms.ollama import OllamaConfig
from memb.configs.llms.openai import OpenAIConfig
from memb.configs.llms.vllm import VllmConfig
from memb.configs.llms.xai import XAIConfig
from memb.configs.rerankers.base import BaseRerankerConfig
from memb.configs.rerankers.cohere import CohereRerankerConfig
from memb.configs.rerankers.huggingface import HuggingFaceRerankerConfig
from memb.configs.rerankers.llm import LLMRerankerConfig
from memb.configs.rerankers.sentence_transformer import SentenceTransformerRerankerConfig
from memb.configs.rerankers.zero_entropy import ZeroEntropyRerankerConfig
from memb.embeddings.mock import MockEmbeddings


def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class LlmFactory:
    """
    Factory for creating LLM instances with appropriate configurations.
    Supports both old-style BaseLlmConfig and new provider-specific configs.
    """

    # Provider mappings with their config classes
    provider_to_class = {
        "ollama": ("memb.llms.ollama.OllamaLLM", OllamaConfig),
        "openai": ("memb.llms.openai.OpenAILLM", OpenAIConfig),
        "groq": ("memb.llms.groq.GroqLLM", BaseLlmConfig),
        "together": ("memb.llms.together.TogetherLLM", BaseLlmConfig),
        "aws_bedrock": ("memb.llms.aws_bedrock.AWSBedrockLLM", AWSBedrockConfig),
        "litellm": ("memb.llms.litellm.LiteLLM", BaseLlmConfig),
        "azure_openai": ("memb.llms.azure_openai.AzureOpenAILLM", AzureOpenAIConfig),
        "openai_structured": ("memb.llms.openai_structured.OpenAIStructuredLLM", OpenAIConfig),
        "anthropic": ("memb.llms.anthropic.AnthropicLLM", AnthropicConfig),
        "azure_openai_structured": ("memb.llms.azure_openai_structured.AzureOpenAIStructuredLLM", AzureOpenAIConfig),
        "gemini": ("memb.llms.gemini.GeminiLLM", GeminiConfig),
        "deepseek": ("memb.llms.deepseek.DeepSeekLLM", DeepSeekConfig),
        "minimax": ("memb.llms.minimax.MiniMaxLLM", MinimaxConfig),
        "xai": ("memb.llms.xai.XAILLM", XAIConfig),
        "sarvam": ("memb.llms.sarvam.SarvamLLM", BaseLlmConfig),
        "lmstudio": ("memb.llms.lmstudio.LMStudioLLM", LMStudioConfig),
        "vllm": ("memb.llms.vllm.VllmLLM", VllmConfig),
        "langchain": ("memb.llms.langchain.LangchainLLM", BaseLlmConfig),
    }

    @classmethod
    def create(cls, provider_name: str, config: Optional[Union[BaseLlmConfig, Dict]] = None, **kwargs):
        """
        Create an LLM instance with the appropriate configuration.

        Args:
            provider_name (str): The provider name (e.g., 'openai', 'anthropic')
            config: Configuration object or dict. If None, will create default config
            **kwargs: Additional configuration parameters

        Returns:
            Configured LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider_name not in cls.provider_to_class:
            raise ValueError(f"Unsupported Llm provider: {provider_name}")

        class_type, config_class = cls.provider_to_class[provider_name]
        llm_class = load_class(class_type)

        # Handle configuration
        if config is None:
            # Create default config with kwargs
            config = config_class(**kwargs)
        elif isinstance(config, dict):
            # Merge dict config with kwargs
            config.update(kwargs)
            config = config_class(**config)
        elif isinstance(config, BaseLlmConfig):
            # Convert base config to provider-specific config if needed
            if config_class != BaseLlmConfig:
                # Convert to provider-specific config
                config_dict = {
                    "model": config.model,
                    "temperature": config.temperature,
                    "api_key": config.api_key,
                    "max_tokens": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                    "enable_vision": config.enable_vision,
                    "vision_details": config.vision_details,
                    "http_client_proxies": config.http_client_proxies,
                }
                # Only forward reasoning fields to provider configs that accept them
                # (explicitly or via **kwargs); others would raise on unexpected kwargs.
                params = inspect.signature(config_class).parameters
                accepts_kwargs = any(p.kind == p.VAR_KEYWORD for p in params.values())
                if accepts_kwargs or "reasoning_effort" in params:
                    config_dict["reasoning_effort"] = config.reasoning_effort
                if accepts_kwargs or "is_reasoning_model" in params:
                    config_dict["is_reasoning_model"] = config.is_reasoning_model
                config_dict.update(kwargs)
                config = config_class(**config_dict)
            else:
                # Use base config as-is
                pass
        else:
            # Assume it's already the correct config type
            pass

        return llm_class(config)

    @classmethod
    def register_provider(cls, name: str, class_path: str, config_class=None):
        """
        Register a new provider.

        Args:
            name (str): Provider name
            class_path (str): Full path to LLM class
            config_class: Configuration class for the provider (defaults to BaseLlmConfig)
        """
        if config_class is None:
            config_class = BaseLlmConfig
        cls.provider_to_class[name] = (class_path, config_class)

    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Get list of supported providers.

        Returns:
            list: List of supported provider names
        """
        return list(cls.provider_to_class.keys())


class EmbedderFactory:
    provider_to_class = {
        "openai": "memb.embeddings.openai.OpenAIEmbedding",
        "ollama": "memb.embeddings.ollama.OllamaEmbedding",
        "huggingface": "memb.embeddings.huggingface.HuggingFaceEmbedding",
        "azure_openai": "memb.embeddings.azure_openai.AzureOpenAIEmbedding",
        "gemini": "memb.embeddings.gemini.GoogleGenAIEmbedding",
        "vertexai": "memb.embeddings.vertexai.VertexAIEmbedding",
        "together": "memb.embeddings.together.TogetherEmbedding",
        "lmstudio": "memb.embeddings.lmstudio.LMStudioEmbedding",
        "langchain": "memb.embeddings.langchain.LangchainEmbedding",
        "aws_bedrock": "memb.embeddings.aws_bedrock.AWSBedrockEmbedding",
        "fastembed": "memb.embeddings.fastembed.FastEmbedEmbedding",
        "local_onnx": "memb.embeddings.local_onnx.LocalONNXEmbedding",
    }

    @classmethod
    def create(cls, provider_name, config, vector_config: Optional[dict]):
        if provider_name == "upstash_vector" and vector_config and vector_config.enable_embeddings:
            return MockEmbeddings()
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            embedder_instance = load_class(class_type)
            base_config = BaseEmbedderConfig(**config)
            return embedder_instance(base_config)
        else:
            raise ValueError(f"Unsupported Embedder provider: {provider_name}")


class VectorStoreFactory:
    provider_to_class = {
        "qdrant": "memb.vector_stores.qdrant.Qdrant",
        "chroma": "memb.vector_stores.chroma.ChromaDB",
        "pgvector": "memb.vector_stores.pgvector.PGVector",
        "milvus": "memb.vector_stores.milvus.MilvusDB",
        "upstash_vector": "memb.vector_stores.upstash_vector.UpstashVector",
        "azure_ai_search": "memb.vector_stores.azure_ai_search.AzureAISearch",
        "azure_mysql": "memb.vector_stores.azure_mysql.AzureMySQL",
        "pinecone": "memb.vector_stores.pinecone.PineconeDB",
        "mongodb": "memb.vector_stores.mongodb.MongoDB",
        "redis": "memb.vector_stores.redis.RedisDB",
        "valkey": "memb.vector_stores.valkey.ValkeyDB",
        "databricks": "memb.vector_stores.databricks.Databricks",
        "elasticsearch": "memb.vector_stores.elasticsearch.ElasticsearchDB",
        "vertex_ai_vector_search": "memb.vector_stores.vertex_ai_vector_search.GoogleMatchingEngine",
        "opensearch": "memb.vector_stores.opensearch.OpenSearchDB",
        "supabase": "memb.vector_stores.supabase.Supabase",
        "weaviate": "memb.vector_stores.weaviate.Weaviate",
        "faiss": "memb.vector_stores.faiss.FAISS",
        "langchain": "memb.vector_stores.langchain.Langchain",
        "s3_vectors": "memb.vector_stores.s3_vectors.S3Vectors",
        "baidu": "memb.vector_stores.baidu.BaiduDB",
        "cassandra": "memb.vector_stores.cassandra.CassandraDB",
        "neptune": "memb.vector_stores.neptune_analytics.NeptuneAnalyticsVector",
        "turbopuffer": "memb.vector_stores.turbopuffer.TurbopufferDB",
        "numpy_flat": "memb.vector_stores.numpy_flat.NumPyFlat",
    }

    @classmethod
    def create(cls, provider_name, config):
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            if not isinstance(config, dict):
                config = config.model_dump()
            vector_store_instance = load_class(class_type)
            return vector_store_instance(**config)
        else:
            raise ValueError(f"Unsupported VectorStore provider: {provider_name}")

    @classmethod
    def reset(cls, instance):
        instance.reset()
        return instance


class RerankerFactory:
    """
    Factory for creating reranker instances with appropriate configurations.
    Supports provider-specific configs following the same pattern as other factories.
    """

    # Provider mappings with their config classes
    provider_to_class = {
        "cohere": ("memb.reranker.cohere_reranker.CohereReranker", CohereRerankerConfig),
        "sentence_transformer": (
            "memb.reranker.sentence_transformer_reranker.SentenceTransformerReranker",
            SentenceTransformerRerankerConfig,
        ),
        "zero_entropy": ("memb.reranker.zero_entropy_reranker.ZeroEntropyReranker", ZeroEntropyRerankerConfig),
        "llm_reranker": ("memb.reranker.llm_reranker.LLMReranker", LLMRerankerConfig),
        "huggingface": ("memb.reranker.huggingface_reranker.HuggingFaceReranker", HuggingFaceRerankerConfig),
    }

    @classmethod
    def create(cls, provider_name: str, config: Optional[Union[BaseRerankerConfig, Dict]] = None, **kwargs):
        """
        Create a reranker instance based on the provider and configuration.

        Args:
            provider_name: The reranker provider (e.g., 'cohere', 'sentence_transformer')
            config: Configuration object or dictionary
            **kwargs: Additional configuration parameters

        Returns:
            Reranker instance configured for the specified provider

        Raises:
            ImportError: If the provider class cannot be imported
            ValueError: If the provider is not supported
        """
        if provider_name not in cls.provider_to_class:
            raise ValueError(f"Unsupported reranker provider: {provider_name}")

        class_path, config_class = cls.provider_to_class[provider_name]

        # Handle configuration
        if config is None:
            config = config_class(**kwargs)
        elif isinstance(config, dict):
            config = config_class(**config, **kwargs)
        elif not isinstance(config, BaseRerankerConfig):
            raise ValueError(f"Config must be a {config_class.__name__} instance or dict")

        # Import and create the reranker class
        try:
            reranker_class = load_class(class_path)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import reranker for provider '{provider_name}': {e}")

        return reranker_class(config)
