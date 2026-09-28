import pytest

from keys.api import Forbidden, Platform, UNDO_WINDOW
from keys.gate import Gate, NeedsApproval
from keys.replay import ADMIN, VOLUME, build, find_token, REPO

_, SECRET = find_token(REPO)


def test_agent_finds_the_domains_token():
    assert find_token(REPO) == ("scripts/add-domain.sh", "rw_domains_4b91e7")


def test_any_token_deletes_everything_by_default():
    api = build()
    assert "12 backups" in api.mutate(SECRET, "volumeDelete", volume_id=VOLUME)
    assert api.rows(VOLUME) == 0


def test_scoped_domains_token_cannot_delete():
    api = build(scoped=True)
    with pytest.raises(Forbidden, match="403"):
        api.mutate(SECRET, "volumeDelete", volume_id=VOLUME)
    assert api.rows(VOLUME) == 48_210


def test_scoped_token_still_does_its_job():
    api = build(scoped=True)
    assert api.mutate(SECRET, "customDomainCreate", domain="rentals.example.com")


def test_gate_holds_delete_until_a_human_approves():
    api = build()
    gate = Gate(api)
    with pytest.raises(NeedsApproval):
        gate.mutate(SECRET, "volumeDelete", volume_id=VOLUME)
    assert api.rows(VOLUME) == 48_210
    gate.approve("volumeDelete", volume_id=VOLUME)
    gate.mutate(SECRET, "volumeDelete", volume_id=VOLUME)
    assert api.rows(VOLUME) == 0


def test_delayed_delete_can_be_undone_inside_the_window():
    api = build(delayed=True)
    api.mutate(SECRET, "volumeDelete", volume_id=VOLUME)
    assert api.rows(VOLUME) == 0
    api.mutate(ADMIN, "volumeRestore", volume_id=VOLUME)
    assert api.rows(VOLUME) == 48_210


def test_delayed_delete_is_final_after_the_window():
    now = [0]
    api = Platform(delayed_delete=True, clock=lambda: now[0])
    api.add_volume("v1", "pg-data", ["production"], rows=10)
    api.add_token("t", "admin", {"volumes:delete"})
    api.mutate("t", "volumeDelete", volume_id="v1")
    now[0] = UNDO_WINDOW + 1
    with pytest.raises(Forbidden, match="window closed"):
        api.mutate("t", "volumeRestore", volume_id="v1")
