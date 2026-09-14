"""
Unit tests for Fast Intent Router.
"""

from core.router import route_intent

def test_route_simple_lock():
    res = route_intent("lock my screen")
    assert res["type"] == "SIMPLE"
    assert res["tool"] == "lock_screen"

def test_route_simple_volume():
    res = route_intent("turn the volume up")
    assert res["type"] == "SIMPLE"
    assert res["tool"] == "set_volume"
    assert res["params"]["action"] == "up"

def test_route_simple_screenshot():
    res = route_intent("take a screenshot")
    assert res["type"] == "SIMPLE"
    assert res["tool"] == "take_screenshot"

def test_route_complex():
    res = route_intent("I am going to study, open my books and turn off music")
    assert res["type"] == "COMPLEX"
    assert "query" in res

def test_route_identity_query():
    res = route_intent("who am i talking to right now?")
    assert res["type"] == "CONVERSATION"
    assert "JARVIS" in res["response"]
    assert "LEO" in res["response"]

def test_route_capabilities_query():
    res = route_intent("what can you do?")
    assert res["type"] == "CONVERSATION"
    assert "Obsidian" in res["response"] or "desktop" in res["response"]

def test_route_greetings():
    res = route_intent("good morning")
    assert res["type"] == "GREETING"
    assert "Gowtham" in res["response"]
