import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from network_ops_dashboard.reports.circuits.models import CircuitProvider

@pytest.mark.django_db
def test_circuitprovider_list_view(client):
    user = User.objects.create_user(username='tester', password='password')
    CircuitProvider.objects.create(name='ATT', email_folder='att_folder')

    client.login(username='tester', password='password')
    response = client.get(reverse('circuitprovider'))

    assert response.status_code == 200
    assert 'ATT' in response.content.decode()