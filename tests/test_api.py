import json
from app import app

def test_offers_endpoint():
    client = app.test_client()
    resp = client.get('/api/offers')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'count' in data and 'offers' in data
    assert data['count'] == len(data['offers'])

def test_estimated_profit_calculation():
    client = app.test_client()
    resp = client.get('/api/offers')
    data = resp.get_json()
    offers = data['offers']
    for o in offers:
        expected = round(float(o.get('payout', 0)) * float(o.get('conversion_rate', 0)), 4)
        assert o.get('estimated_profit_per_action') == expected
