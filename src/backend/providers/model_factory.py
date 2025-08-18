from typing import Optional, List, Dict, Any, Union
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from core.config import settings


class LLM:
    def __init__(
        self, name: str, provider: Optional[str] = None, temperature: float = 0.2
    ):
        self.name = name
        self.provider = provider
        self.temperature = temperature

        self._model = init_chat_model(
            name,
            model_provider=provider,
            temperature=temperature,
        )

    @staticmethod
    def _to_lc_messages(messages: List[Dict[str, Any]]):
        lc_msgs = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                lc_msgs.append(HumanMessage(content=content))
            else:
                if role == "system":
                    lc_msgs.append(SystemMessage(content=str(content)))
                else:
                    lc_msgs.append(HumanMessage(content=str(content)))
        return lc_msgs

    async def ask(self, messages: List[Dict[str, Any]]) -> str:
        """
        messages: list of {role: 'system'|'user', content: str|multimodal content}
        returns: string content from the model
        """
        out = await self._model.ainvoke(self._to_lc_messages(messages))
        return getattr(out, "content", str(out)).strip()


class ModelFactory:
    """Factory / Strategy for selecting base and stronger models, both text and vision."""

    @staticmethod
    def text_default() -> LLM:
        return LLM(
            name=settings.llm_text_model,
            provider=settings.llm_text_provider or None,
            temperature=0.2,
        )

    @staticmethod
    def text_stronger() -> LLM:
        return LLM(
            name=settings.llm_text_stronger_model,
            provider=settings.llm_text_provider or None,
            temperature=0.2,
        )

    @staticmethod
    def vision_default() -> LLM:
        return LLM(
            name=settings.llm_vision_model,
            provider=settings.llm_vision_provider or settings.llm_text_provider or None,
            temperature=0.2,
        )

    @staticmethod
    def vision_stronger() -> LLM:
        return LLM(
            name=settings.llm_vision_stronger_model,
            provider=settings.llm_vision_provider or settings.llm_text_provider or None,
            temperature=0.2,
        )
