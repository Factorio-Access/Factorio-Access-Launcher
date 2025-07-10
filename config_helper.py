import config as _config
from typing import Protocol as _Protocol


class base_settings(object):
    _cat: str
    _config_manager: "_config.Conf_Editor"

    def __init__(self, cat: str, config_manger: "_config.Conf_Editor"):
        super().__setattr__("_cat", cat)
        super().__setattr__("_config_manager", config_manger)

    def __getattr__(self, name: str):
        return (
            super()
            .__getattribute__("_config_manager")
            .get_setting(self._cat, name.replace("_", "-"))
        )

    def __setattr__(self, name, value):
        super().__getattribute__("_config_manager").set_setting(
            self._cat, name.replace("_", "-"), value
        )
