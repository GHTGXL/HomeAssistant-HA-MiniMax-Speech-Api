import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_API_KEY

DOMAIN = "minimax_tts"
CONF_GROUP_ID = "group_id"
CONF_VOICE_ID = "voice_id"

class MinimaxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Minimax TTS", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_GROUP_ID): str,
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_VOICE_ID, default="mos_audio_35005847-4600-11f0-990d-c66847954116"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)