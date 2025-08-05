import pytest
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from django.utils import timezone
from network_ops_dashboard import settings
from network_ops_dashboard.asavpn.models import AsaVpnDiscoLog, AsaVpnConnectedUsers

@pytest.mark.django_db
def test_asavpn_discolog_creation_and_str():
    log = AsaVpnDiscoLog.objects.create(username="jdoe001", logoutput="User disconnected by admin")
    assert log.username == "jdoe001"
    assert "jdoe001 - User disconnected" in str(log)

@pytest.mark.django_db
def test_asavpn_discolog_ordering():
    AsaVpnDiscoLog.objects.create(username="auser001", logoutput="zzz")
    AsaVpnDiscoLog.objects.create(username="buser001", logoutput="aaa")
    logs = AsaVpnDiscoLog.objects.all()
    assert logs[0].logoutput == "aaa"
    assert logs[1].logoutput == "zzz"

@pytest.mark.django_db
def test_asavpn_connected_users_creation_and_str():
    user = AsaVpnConnectedUsers.objects.create(name="fw1", connected="10", load="15%")
    assert user.name == "fw1"
    assert str(user) == "fw1"

@pytest.mark.django_db
def test_asavpn_connected_users_ordering():
    AsaVpnConnectedUsers.objects.create(name="fw-b", connected="20", load="30%")
    AsaVpnConnectedUsers.objects.create(name="fw-a", connected="10", load="15%")
    users = AsaVpnConnectedUsers.objects.all()
    assert users[0].name == "fw-a"
    assert users[1].name == "fw-b"