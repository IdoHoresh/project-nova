def test_main_imports() -> None:
    import nova_agent.main as m

    assert callable(m.run)
    assert callable(m.cli)
