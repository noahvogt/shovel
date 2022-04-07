import os
import log

def get_xdg_dir(env_var: str, fallback_dir: str, home: str):
    xdg_dir = os.getenv(env_var)
    if xdg_dir is None or xdg_dir == "":
        xdg_dir = "{}/{}".format(home, fallback_dir)

    return xdg_dir


def get_configured_dirs():
    log.msg("checking configured directories")
    home = os.getenv("HOME")
    if home is None or home == "":
        log.error_exit("$HOME not accessible")

    xdg_data_home = get_xdg_dir("XDG_DATA_HOME", ".local/share", home)
    xdg_config_home = get_xdg_dir("XDG_CONFIG_HOME", ".config", home)
    xdg_cache_home = get_xdg_dir("XDG_CACHE_HOME", ".cache", home)

    return {"src_dir" : "{}/shovel/src".format(xdg_data_home),
            "build_dir" : "{}/shovel/build".format(xdg_data_home),
            "config_dir" : "{}/shovel".format(xdg_config_home),
            "cache_dir" : "{}/shovel".format(xdg_cache_home),
            "rule_dir" : "{}/shovel/rules".format(xdg_data_home)}


def check_for_write_permissions(config_dirs: dict):
    for path in config_dirs:
        if not os.access(config_dirs[path], os.R_OK):
            log.error_exit("cannot access directory '{}', please check".format(
                           config_dirs[path]) + "your permissions")


def get_rules(rule_dir):
    log.msg("getting rules")
    rules = []
    for (_, subdirs, filenames) in os.walk(rule_dir):
        if len(subdirs) > 0:
            log.msg("warning: subdirectories in '{}' are ignored:".format(
                    rule_dir), "warning")
            for subdir in subdirs:
                print(subdir)
        rules.extend(filenames)
        break

    return rules


class Config:
    def __init__(self):
        self.config_dirs = get_configured_dirs()
        self.rules = get_rules(self.config_dirs.get("rule_dir"))
        log.msg("configuration initialized", "success")

    def parse(self):
        #parse_config()
        check_for_write_permissions(self.config_dirs)


    def update(self):
        self.config_dirs = get_configured_dirs()
        self.rules = get_rules(self.config_dirs.get("rule_dir"))
        log.msg("updated rules and directory configurations", "success")
