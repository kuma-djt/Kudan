from app.broker import BrokerMock


def test_broker_mock_order_changes_position() -> None:
    broker = BrokerMock()
    broker.place_order("BTCUSD", "buy", 1.0, "market")
    positions = broker.get_positions()
    assert positions[0]["symbol"] == "BTCUSD"
    assert positions[0]["qty"] == 1.0
