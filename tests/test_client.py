import pytest
from unittest.mock import MagicMock

from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter

from iredis.client import Client
from iredis.completers import completer_mapping
from iredis.redis_grammar import get_command_grammar
from iredis.entry import Rainbow, prompt_message
from iredis.config import config


@pytest.mark.parametrize(
    "_input, command_name, expect_args",
    [
        ("keys *", "keys", ["*"]),
        ("DEL abc foo bar", "DEL", ["abc", "foo", "bar"]),
        ("cluster info", "cluster info", []),
        ("CLUSTER failover FORCE", "CLUSTER failover", ["FORCE"]),
    ],
)
def test_send_command(_input, command_name, expect_args):
    client = Client("127.0.0.1", "6379", None)
    client.execute_command_and_read_response = MagicMock()
    next(client.send_command(_input, None))
    args, kwargs = client.execute_command_and_read_response.call_args
    assert args == (None, command_name, *expect_args)


def test_patch_completer():
    client = Client("127.0.0.1", "6379", None)
    grammar = get_command_grammar("MGET")
    completer = GrammarCompleter(grammar, completer_mapping)
    client.pre_hook(
        "MGET foo bar hello world", "MGET", "foo bar hello world", completer
    )
    assert completer.completers["key"].words == ["world", "hello", "bar", "foo"]
    assert completer.completers["keys"].words == ["world", "hello", "bar", "foo"]

    grammar = get_command_grammar("GET")
    completer = GrammarCompleter(grammar, completer_mapping)
    client.pre_hook("GET bar", "GET", "bar", completer)
    assert completer.completers["keys"].words == ["bar", "world", "hello", "foo"]


def test_get_server_verison_after_client():

    Client("127.0.0.1", "6379", None)
    assert config.version.startswith("5.")

    config.version = "Unknown"
    Client("127.0.0.1", "6379", None, get_info=False)
    assert config.version == "Unknown"


def test_do_help():

    client = Client("127.0.0.1", "6379", None)
    config.version = "5.0.0"
    resp = client.do_help("SET")
    assert resp[10] == ("", "1.0.0 (Avaiable on your redis-server: 5.0.0)")
    config.version = "2.0.0"
    resp = client.do_help("cluster", "addslots")
    assert resp[10] == ("", "3.0.0 (Not avaiable on your redis-server: 2.0.0)")


def test_rainbow_iterator():
    "test color infinite iterator"
    original_color = Rainbow.color
    Rainbow.color = list(range(0, 3))
    assert list(zip(range(10), Rainbow())) == [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 1),
        (4, 0),
        (5, 1),
        (6, 2),
        (7, 1),
        (8, 0),
        (9, 1),
    ]
    Rainbow.color = original_color


def test_prompt_message(iredis_client):
    original_rainbow = config.rainbow
    config.rainbow = False
    assert prompt_message(iredis_client) == "127.0.0.1:6379> "

    config.rainbow = True
    assert prompt_message(iredis_client)[:3] == [
        ("#cc2244", "1"),
        ("#bb4444", "2"),
        ("#996644", "7"),
    ]
    config.rainbow = original_rainbow
