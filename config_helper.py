import config as _config

class my_awesome_getter_setter(object):
    def __getattribute__(self, __name: str) -> str:
        return _config.current_conf.get_setting(*(super().__getattribute__(__name)))
    def __setattr__(self, __name: str, __value: str) -> None:
        _config.current_conf.set_setting(*super().__getattribute__(__name),__value)