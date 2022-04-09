import os
import re
from abc import ABC, abstractmethod

import log

def get_xdg_dir(env_var: str, fallback_dir: str, home):
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
                           config_dirs[path]) + " for write permissions")


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

def read_config_file(file):
    raw_lines = []
    try:
        with open(file, encoding="utf8", mode="r") as reader:
            raw_lines = reader.readlines()
        reader.close()

    except FileNotFoundError:
        log.error_exit("config file not found")
    except PermissionError:
        log.error_exit("config not accessible, please check your permissions")

    return raw_lines

class Validator(ABC): #pylint: disable=R0903
    @abstractmethod
    def validate(self, value) -> bool:
        pass

class SSHKeyValidator(Validator): #pylint: disable=R0903
    def validate(self, value: str) -> bool:
        try:
            with open(value, encoding="utf8", mode="r") as reader:
                reader.readlines()
            reader.close()

        except FileNotFoundError:
            log.error_exit("ssh key file not found", do_exit=False)
            return False
        except PermissionError:
            log.error_exit("ssh key not accessible, please check your"
                           " permissions", do_exit=False)
            return False

        return True

class IntervalValidator(Validator): #pylint: disable=R0903
    def validate(self, value: str) -> bool:
        try:
            if int(value) is int:
                return True
        except (ValueError, KeyError):
            log.error_exit("please provide the inverval as an integer",
                           do_exit=False)
        return False


class GithubUserValidator(Validator): #pylint: disable=R0903
    def validate(self, value: str) -> bool:
        return bool(re.match("[a-zA-Z0-9]+[a-zA-Z0-9\\-]*[a-zA-Z0-9]+", value))


# assumes same rules as github
class AURUserValidator(Validator): #pylint: disable=R0903
    def validate(self, value: str) -> bool:
        return bool(re.match("[a-zA-Z0-9]+[a-zA-Z0-9\\-]*[a-zA-Z0-9]+", value))


class PidFileValidator(Validator): #pylint: disable=R0903
    def validate(self, value: str) -> bool:
        if value not in ["yes", "no"]:
            log.error_exit("invalid option, use 'yes' or 'no'", do_exit=False)
            return False
        return True


def is_valid_config_entry(validator, value) -> bool:
    return validator.validate("hey", value)


def config_entry(value: str, is_obligatory: bool, config_str: str,
                 validator):
    return {"value" : value, "is_obligatory": is_obligatory, "validator" :
            validator, "config_str" : config_str}


def get_empty_config_state() -> dict:
    return {"ssh_key_location" : config_entry("", True, "ssh-key",
                                 SSHKeyValidator),
            "interval" : config_entry("", True, "interval", IntervalValidator),
            "github_user" : config_entry("", True, "github",
                            GithubUserValidator),
            "aur_user" : config_entry("", True, "aur", AURUserValidator),
            "use_pid_file" : config_entry("no", False, "use-pid-file",
                             PidFileValidator)}

def is_empty_or_comment_line(line: str):
    return (re.match("^\\s*#", line) or re.match("^\\s*$", line))

class ConfigParser:
    def __init__(self):
        self.config_dirs = get_configured_dirs()
        self.rules = get_rules(self.config_dirs.get("rule_dir"))
        self.config_state: dict = get_empty_config_state()
        log.msg("configuration initialized", "success")


    def update(self):
        self.config_dirs = get_configured_dirs()
        self.rules = get_rules(self.config_dirs.get("rule_dir"))
        log.msg("updated rules and directory configurations", "success")


    def get_config_file(self):
        return read_config_file(str(self.config_dirs.get("config_dir")) +
                                "/config")

    #def get_option_from_config_str(self, config_str: str):


    def parse_config_file(self):
        log.msg("parsing config file")
        file_content = self.get_config_file()
        for index, line in enumerate(file_content):

            if is_empty_or_comment_line(line):
                continue

            if line.endswith("\n"):
                line = line[:-1]

            if not re.match("^\\s*[a-z\\-]+\\s*=\\s*\\S*\\s*$", line):
                log.error_exit("wrong config format on line {}: {}".format(
                               index + 1, line))

            config_str = str(line[:line.find("=")]).strip()
            value = str(line[line.find("=") + 1:]).strip()
            full_config_name = ""

            for item in self.config_state.items():
                if config_str == item[1]["config_str"]:
                    full_config_name = item[0]
                    break
            else:
                log.error_exit("'{}' on line {} is not a valid option".format(
                               config_str, index))

            if not is_valid_config_entry((self.config_state.get(
                   full_config_name).get("validator")), value):
                log.error_exit("configuration entry for '{}' is invalid.".
                               format(config_str))


            self.config_state.get(full_config_name)["value"] = value
            #validate_config_entry(SSHKeyValidato#r, value)
            #if self.config_state.get(full_config_name).get("options") is not None:
            #    print("checking options for " + config_str + line)


            #print(config_str)
            #print(value)
            #print(full_config_name)


    def parse(self):
        log.msg("parsing configuration")
        check_for_write_permissions(self.config_dirs)
        self.parse_config_file()
