import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from network_ops_dashboard import settings
from network_ops_dashboard.asavpn.models import AsaVpnDiscoLog
from network_ops_dashboard.models import SiteSecrets
from unittest.mock import patch

@pytest.fixture
def authenticated_client(db, client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.login(username="testuser", password="testpass")
    return client

@pytest.mark.django_db
def test_findanddisco_view_auth_required(client):
    response = client.get(reverse('asavpn_findanddiscouser'))
    assert response.status_code == 302

@pytest.mark.django_db
def test_findanddisco_view_get(authenticated_client):
    SiteSecrets.objects.create(varname='asavpn_primary_user', varvalue='svc_act')
    response = authenticated_client.get(reverse('asavpn_findanddiscouser'))
    assert response.status_code == 200
    assert b'<form' in response.content

@patch('network_ops_dashboard.asavpn.views.findVPNuser')
def test_findanddisco_view_post(mock_findvpn, authenticated_client):
    SiteSecrets.objects.create(varname='asavpn_primary_user', varvalue='svc_act')
    mock_findvpn.return_value = 'Disconnected user successfully'
    data = {
        'targetUser': 'jdoe001',
        'username1': 'admin',
        'password1': 'pass123',
        'targetAction': 'True'
    }
    response = authenticated_client.post(reverse('asavpn_findanddiscouser'), data)
    assert response.status_code == 200
    assert b'Disconnected user successfully' in response.content

@pytest.mark.django_db
def test_disco_log_view(authenticated_client):
    AsaVpnDiscoLog.objects.create(username='jdoe001', logoutput='kicked')
    response = authenticated_client.get(reverse('asavpn_findanddiscouser_log'))
    assert response.status_code == 200
    assert b'jdoe001' in response.content

@pytest.mark.django_db
def test_disco_log_all_view(authenticated_client):
    AsaVpnDiscoLog.objects.create(username='jdoe001', logoutput='kicked')
    AsaVpnDiscoLog.objects.create(username='mdoe291', logoutput='expired')
    response = authenticated_client.get(reverse('asavpn_findanddiscouser_log_all'))
    assert response.status_code == 200
    assert b'jdoe001' in response.content and b'mdoe291' in response.content