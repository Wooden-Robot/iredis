import pytest
import tempfile
from unittest.mock import patch

from iredis.entry import gather_args, parse_url, DSN, SkipAuthFileHistory


@pytest.mark.parametrize(
    "is_tty,raw_arg_is_raw,final_config_is_raw",
    [
        (True, None, False),
        (True, True, True),
        (True, False, False),
        (False, None, True),
        (False, True, True),
        (False, False, True),  # not tty
    ],
)
def test_command_entry_tty(is_tty, raw_arg_is_raw, final_config_is_raw, config):
    # is tty + raw -> raw
    with patch("sys.stdout.isatty") as patch_tty:

        patch_tty.return_value = is_tty
        if raw_arg_is_raw is None:
            call = ["iredis"]
        elif raw_arg_is_raw is True:
            call = ["iredis", "--raw"]
        elif raw_arg_is_raw is False:
            call = ["iredis", "--no-raw"]
        else:
            raise Exception()
        gather_args.main(call, standalone_mode=False)
        assert config.raw == final_config_is_raw


def test_command_with_decode_utf_8():
    from iredis.config import config

    gather_args.main(["iredis", "--decode", "utf-8"], standalone_mode=False)
    assert config.decode == "utf-8"

    gather_args.main(["iredis"], standalone_mode=False)
    assert config.decode == ""


def test_command_with_shell_pipeline():
    from iredis.config import config

    config.shell = True
    gather_args.main(["iredis", "--no-shell"], standalone_mode=False)
    assert config.shell is False

    config.shell = False
    gather_args.main(["iredis"], standalone_mode=False)
    assert config.shell is True


@pytest.mark.parametrize(
    "url,dsn",
    [
        (
            "redis://localhost:6379/3",
            DSN(
                scheme="redis",
                host="localhost",
                port=6379,
                path=None,
                db=3,
                username=None,
                password=None,
            ),
        ),
        (
            "redis://localhost:6379",
            DSN(
                scheme="redis",
                host="localhost",
                port=6379,
                path=None,
                db=0,
                username=None,
                password=None,
            ),
        ),
        (
            "rediss://localhost:6379",
            DSN(
                scheme="rediss",
                host="localhost",
                port=6379,
                path=None,
                db=0,
                username=None,
                password=None,
            ),
        ),
        (
            "redis://username:password@localhost:6379",
            DSN(
                scheme="redis",
                host="localhost",
                port=6379,
                path=None,
                db=0,
                username="username",
                password="password",
            ),
        ),
        (
            "redis://:password@localhost:6379",
            DSN(
                scheme="redis",
                host="localhost",
                port=6379,
                path=None,
                db=0,
                username=None,
                password="password",
            ),
        ),
        (
            "redis://username@localhost:12345",
            DSN(
                scheme="redis",
                host="localhost",
                port=12345,
                path=None,
                db=0,
                username="username",
                password=None,
            ),
        ),
        (
            # query string won't work for redis://
            "redis://username@localhost:6379?db=2",
            DSN(
                scheme="redis",
                host="localhost",
                port=6379,
                path=None,
                db=0,
                username="username",
                password=None,
            ),
        ),
        (
            "unix://username:password2@/tmp/to/socket.sock?db=0",
            DSN(
                scheme="unix",
                host=None,
                port=None,
                path="/tmp/to/socket.sock",
                db=0,
                username="username",
                password="password2",
            ),
        ),
        (
            "unix://:password3@/path/to/socket.sock",
            DSN(
                scheme="unix",
                host=None,
                port=None,
                path="/path/to/socket.sock",
                db=0,
                username=None,
                password="password3",
            ),
        ),
        (
            "unix:///tmp/socket.sock",
            DSN(
                scheme="unix",
                host=None,
                port=None,
                path="/tmp/socket.sock",
                db=0,
                username=None,
                password=None,
            ),
        ),
    ],
)
def test_parse_url(url, dsn):
    assert parse_url(url) == dsn


@pytest.mark.parametrize(
    "command,record",
    [
        ("set foo bar", True),
        ("set auth bar", True),
        ("auth 123", False),
        ("AUTH hello", False),
        ("AUTH hello world", False),
    ],
)
def test_history(command, record):
    f = tempfile.TemporaryFile("w+")
    history = SkipAuthFileHistory(f.name)
    assert history._loaded_strings == []
    history.append_string(command)
    assert (command in history._loaded_strings) is record
