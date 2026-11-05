from __future__ import annotations

import json
import os
import sys
import time
from types import SimpleNamespace

import pytest

from apps.signals_app.source import SourceMonitor, snapshot
from apps.signals_app.store import Store
from apps.signals_app.service import AppService
from apps.signals_app import canonical, worker


def test_running_loop_does_not_establish_a_market_connection(tmp_path):
    monitor = SourceMonitor(Store(tmp_path), ['EUR/USD'])
    monitor.cycle({}, now=1000)
    assert snapshot(monitor.store, now=1000)['state'] == 'SOURCE_UNAVAILABLE'
    monitor.cycle({'market_data_state': 'READY', 'last_market_data_success_ts': 1000}, now=1000)
    assert snapshot(monitor.store, now=1000)['state'] == 'SOURCE_UNAVAILABLE'
    assert snapshot(monitor.store, now=1000)['reason'] == 'EVALUATION_NOT_READY'


def test_real_data_and_completed_evaluation_are_both_required(tmp_path):
    monitor = SourceMonitor(Store(tmp_path), ['EUR/USD'])
    monitor.evaluation(SimpleNamespace(kind='NO_SIGNAL'), now=1000)
    monitor.cycle({'market_data_state': 'READY', 'last_market_data_success_ts': 999}, now=1000)
    data = snapshot(monitor.store, now=1000)
    assert data['state'] == 'OBSERVING'
    assert data['last_decision'] == 'NO_SIGNAL'
    assert data['evaluations'] == 1
    assert not data['execution_timing_available']
    assert snapshot(monitor.store, now=1031)['state'] == 'SOURCE_UNAVAILABLE'
    assert snapshot(monitor.store, now=998)['state'] == 'SOURCE_UNAVAILABLE'


@pytest.mark.parametrize(('market','expected'), [
    ('MARKET_DATA_COLLECTING','SOURCE_WARMING'),
    ('MARKET_DATA_LIMITED','SOURCE_LIMITED'),
    ('MARKET_DATA_UNAVAILABLE','SOURCE_UNAVAILABLE')])
def test_upstream_data_problems_do_not_become_healthy_heartbeats(tmp_path, market, expected):
    monitor = SourceMonitor(Store(tmp_path), ['EUR/USD'])
    monitor.evaluation(SimpleNamespace(kind='PRE'), now=1000)
    monitor.cycle({'market_data_state': market, 'last_market_data_success_ts': 1000}, now=1000)
    assert snapshot(monitor.store, now=1000)['state'] == expected


def test_stale_evaluations_and_stale_market_data_cannot_remain_green(tmp_path):
    monitor = SourceMonitor(Store(tmp_path), ['EUR/USD'])
    monitor.evaluation(SimpleNamespace(kind='PRE'), now=1000)
    monitor.cycle({'market_data_state': 'READY', 'last_market_data_success_ts': 1090}, now=1091)
    assert snapshot(monitor.store, now=1091)['state'] == 'SOURCE_UNAVAILABLE'
    monitor.evaluation(SimpleNamespace(kind='PRE'), now=1200)
    monitor.cycle({'market_data_state': 'READY', 'last_market_data_success_ts': 1000}, now=1200)
    assert snapshot(monitor.store, now=1200)['state'] == 'SOURCE_UNAVAILABLE'


def test_minute_wide_scan_cadence_retains_health_until_actual_evidence_expires(tmp_path):
    monitor = SourceMonitor(Store(tmp_path), ['EUR/USD'])
    monitor.evaluation(SimpleNamespace(kind='NO_SIGNAL'), now=1000)
    monitor.cycle({'market_data_state':'READY','last_market_data_success_ts':1000}, now=1060)
    assert snapshot(monitor.store, now=1060)['state'] == 'OBSERVING'
    monitor.evaluation_failed = True
    monitor.cycle({'market_data_state':'READY','last_market_data_success_ts':1060}, now=1060)
    assert snapshot(monitor.store, now=1060)['state'] == 'SOURCE_UNAVAILABLE'


def test_history_transport_requests_utc_without_changing_authentication_or_shared_client():
    calls = []
    delegate = SimpleNamespace(get=lambda url, **kw: calls.append((url,kw)), exceptions=object())
    adapter = worker.UtcMarketHttp(delegate, 'https://provider.invalid/time_series')
    params = {'apikey':'fixture-only','symbol':'EUR/USD'}
    adapter.get('https://provider.invalid/time_series',params=params,timeout=20)
    assert calls[0][1]['params'] == dict(params,timezone='UTC')
    assert params == {'apikey':'fixture-only','symbol':'EUR/USD'}
    assert calls[0][1]['timeout'] == 20
    assert adapter.exceptions is delegate.exceptions
    adapter.get('https://provider.invalid/other',params=params)
    assert calls[1][1]['params'] is params


def test_source_restart_drops_old_readiness_and_keeps_no_raw_runtime_secrets(tmp_path):
    store = Store(tmp_path)
    monitor = SourceMonitor(store, ['EUR/USD'])
    monitor.evaluation(SimpleNamespace(kind='CONFIRM'), now=1000)
    monitor.cycle({'market_data_state': 'READY', 'last_market_data_success_ts': 1000,
                   'market_data_note': 'secret-api-key-and-provider-url'}, [{'available': True}], now=1000)
    assert snapshot(store, now=1000)['execution_timing_available']
    assert 'secret-api-key' not in json.dumps(snapshot(store, now=1000))
    SourceMonitor(store, ['EUR/USD'])
    data = snapshot(store)
    assert data['state'] == 'STARTING'
    assert data['last_evaluation_at'] is None
    assert not data['execution_timing_available']


def test_old_loop_heartbeat_never_implies_real_market_health(tmp_path):
    store = Store(tmp_path)
    store.set_meta('last_engine_tick', int(time.time()))
    store.set_meta('engine_state', 'OBSERVING')
    assert AppService(store).status()['engine_state'] == 'NOT_CONNECTED'


def test_app_runtime_isolated_and_catalog_selection_preserves_source(tmp_path, monkeypatch):
    source = canonical.SEND/'config'/'active_symbols.json'
    original = source.read_bytes()
    env = dict(os.environ, SIGNALS_APP_SYMBOLS='EUR/USD', TELEGRAM_BOT_TOKEN='do-not-copy',
               FREE_CHANNEL_ID='-1234', ALGO_PARAMS_PATH='/unrelated/algo.json',
               ENGINE_EVENTS_LOG='/unrelated/events.jsonl', OWNER_SIGNAL_DELIVERY_ENABLED='1')
    monkeypatch.setattr(os, 'environ', env)
    engine, symbols = worker.prepare_runtime(tmp_path)
    assert symbols == ['EUR/USD']
    assert source.read_bytes() == original
    selected = json.loads((engine/'config'/'active_symbols.json').read_text())
    assert selected['forex'] == ['EUR/USD'] and selected['crypto'] == []
    assert 'TELEGRAM_BOT_TOKEN' not in env and 'FREE_CHANNEL_ID' not in env
    assert env['ENABLE_TELEGRAM'] == env['ENABLE_BROKER_EXECUTION'] == env['OWNER_SIGNAL_DELIVERY_ENABLED'] == '0'
    for key in ['ALGO_PARAMS_PATH','ENGINE_EVENTS_LOG','DIST_EVENTS_LOG','OUTCOMES_LOG']:
        assert env[key].startswith(str(engine))


def test_unknown_symbol_is_rejected_before_market_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(os, 'environ', dict(os.environ, SIGNALS_APP_SYMBOLS='UNKNOWN/PAIR'))
    with pytest.raises(ValueError, match='existing market catalog'):
        worker.prepare_runtime(tmp_path)


def test_existing_engine_candidate_reaches_app_only_transport(tmp_path, monkeypatch):
    import core
    from core import market_data_provider_control, storage
    from runtime import market_client
    from apps.signals_app.tests.test_app import candidate
    now = int(time.time())
    fake = SimpleNamespace(decide=lambda **kwargs: SimpleNamespace(decision=SimpleNamespace(kind='PRE')),
                           _LAST_CALIBRATION_STATE={})
    def tick(_now):
        fake.decide()
        fake.distribution_router.route(canonical.signal(candidate()), now_ts=now)
    fake.run_once = tick
    monkeypatch.setattr(core, 'signal_engine', fake, raising=False)
    # The worker's HTTP adapter binding must not escape this process-isolation fixture.
    monkeypatch.setattr(market_client, 'requests', market_client.requests)
    monkeypatch.setitem(sys.modules, 'core.signal_engine', fake)
    monkeypatch.setattr(market_data_provider_control, 'get_active_provider', lambda: 'TWELVE_DATA')
    monkeypatch.setattr(market_data_provider_control, 'provider_ready', lambda _: (True,'READY'))
    monkeypatch.setattr(storage, 'load_json', lambda *args, **kwargs: {
        'market_data_state':'READY', 'last_market_data_success_ts':now})
    class EndCycle(BaseException):
        pass
    def end_cycle(_seconds):
        raise EndCycle()
    monkeypatch.setattr(worker.time, 'sleep', end_cycle)
    monkeypatch.setattr(os, 'environ', dict(os.environ, SIGNALS_APP_SYMBOLS='EUR/USD'))
    with pytest.raises(EndCycle):
        worker.run(tmp_path)
    store = Store(tmp_path)
    assert snapshot(store)['state'] == 'OBSERVING'
    assert len(AppService(store).feed('FREE')) == 1
    assert AppService(store).feed('FREE')[0]['stage'] == 'PRE'


def test_owner_dashboard_exposes_source_evidence_but_no_credentials(tmp_path):
    from fastapi.testclient import TestClient
    from apps.signals_app.api import create_app
    app = create_app(tmp_path, public_url='http://testserver', setup_token='long-private-owner-setup-token-for-tests')
    with TestClient(app) as client:
        response = client.post('/api/setup', json={'email':'owner@example.com', 'password':'owner-test-password',
            'token':'long-private-owner-setup-token-for-tests'})
        assert response.status_code == 200
        data = client.get('/api/admin').json()
        assert data['source']['state'] == 'NOT_CONNECTED'
        assert not any(key in json.dumps(data['source']).lower() for key in ['api_key','password','secret'])
