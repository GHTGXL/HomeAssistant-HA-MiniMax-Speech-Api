# /config/custom_components/minimax_tts/tts.py (胜利最终版 V2)

import logging
import requests
import voluptuous as vol

from homeassistant.components.tts import (
    PLATFORM_SCHEMA, Provider, TtsAudioType
)
from homeassistant.const import CONF_API_KEY
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

MINIMAX_API_URL = "https://api.minimax.io/v1/t2a_v2"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("group_id"): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required("voice_id"): cv.string,
    }
)

def get_engine(hass, config, discovery_info=None):
    provider = MinimaxProvider(
        config.get("group_id"),
        config.get(CONF_API_KEY),
        config.get("voice_id"),
    )
    provider.hass = hass
    return provider

class MinimaxProvider(Provider):
    def __init__(self, group_id, api_key, voice_id):
        self._group_id = group_id
        self._api_key = api_key
        self._voice_id = voice_id
        self.name = "Minimax TTS"
        self.hass = None

    @property
    def default_language(self):
        return "zh-cn"

    @property
    def supported_languages(self):
        return ["zh-cn"]
        
    async def async_get_tts_audio(self, message: str, language: str, options: dict | None = None) -> TtsAudioType:
        url = f"{MINIMAX_API_URL}?GroupId={self._group_id}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        # --- 最终修正！我们加回了 model，并使用了正确的 turbo 值！---
        payload = {
            "model": "speech-02-turbo",
            "text": message,
            "voice_setting": {
                "voice_id": self._voice_id
            }
        }
        # --- 修正结束 ---

        _LOGGER.debug("正在向 Minimax 发送 TTS 请求 (最终正确格式): %s", payload)

        def do_request():
            return requests.post(url, headers=headers, json=payload, timeout=20)

        try:
            response = await self.hass.async_add_executor_job(do_request)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _LOGGER.error("调用 Minimax TTS API 时发生网络错误: %s", e)
            try:
                _LOGGER.error("Minimax API 错误详情: %s", e.response.json())
            except:
                pass
            return (None, None)

        content_type = response.headers.get("Content-Type")
        if "audio/" not in content_type:
            _LOGGER.error("Minimax API 返回的不是音频格式。响应: %s", response.text)
            return (None, None)

        return TtsAudioType(content_type, response.content)