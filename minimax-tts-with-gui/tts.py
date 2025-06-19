# tts.py (The Final, True, Corrected Version)
import logging
import requests
from functools import partial

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

DOMAIN = "minimax_tts"
MINIMAX_API_URL = "https://api.minimax.io/v1/t2a_v2"
CONF_GROUP_ID = "group_id"
CONF_VOICE_ID = "voice_id"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Minimax TTS from a config entry."""
    async_add_entities([MinimaxTtsEntity(hass, config_entry)])

class MinimaxTtsEntity(TextToSpeechEntity):
    """The Home Assistant entity for Minimax TTS."""
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self._config_data = config_entry.data
        self._attr_name = f"Minimax TTS {config_entry.title}" # 使用标题来区分
        self._attr_unique_id = config_entry.entry_id

    @property
    def default_language(self) -> str:
        # --- 这是最关键的修正之一！返回一个它支持的语言 ---
        return "zh"
    
    @property
    def supported_languages(self) -> list[str]:
        # --- 这是最关键的、最终的修正！我们声明支持的语言！ ---
        return ["zh", "en", "ja"] # 中文，英文，日文

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "Minimax",
            "model": self._config_data.get(CONF_VOICE_ID)
        }
    
    def get_tts_audio(self, message: str, language: str) -> tuple[str, bytes] | None:
        """This is the synchronous part that runs in the background."""
        group_id = self._config_data[CONF_GROUP_ID]
        api_key = self._config_data[CONF_API_KEY]
        voice_id = self._config_data[CONF_VOICE_ID]

        url = f"{MINIMAX_API_URL}?GroupId={group_id}"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"text": message, "model": "speech-02-turbo", "voice_setting": {"voice_id": voice_id}}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            json_response = response.json()
            
            if json_response.get("base_resp", {}).get("status_code") == 0:
                audio_hex = json_response.get("data", {}).get("audio")
                if audio_hex:
                    audio_bytes = bytes.fromhex(audio_hex)
                    return ("mp3", audio_bytes)
                else:
                    return ("error", "API success response but no audio data found.")
            else:
                error_msg = json_response.get("base_resp", {}).get("status_msg", "Unknown error")
                return ("error", error_msg)

        except requests.exceptions.RequestException as e:
            return ("error", str(e))

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict | None = None
    ) -> tuple[str, bytes] | None:
        """The async wrapper that Home Assistant calls."""
        try:
            result = await self.hass.async_add_executor_job(
                self.get_tts_audio, message, language
            )

            if result is None:
                return None

            result_type, data = result
            
            if result_type == "error":
                _LOGGER.error("Minimax TTS Error: %s", data)
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "persistent_notification", "create", {
                            "title": "Minimax TTS Error",
                            "message": f"Failed to get audio: {data}"
                        }
                    )
                )
                return None
            
            return (result_type, data)

        except Exception as e:
            _LOGGER.error("Unknown error in async_get_tts_audio: %s", e)
            return None