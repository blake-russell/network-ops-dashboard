import pytest
from network_ops_dashboard.reports.circuits.models import CircuitProvider, Circuit, CircuitTag
from network_ops_dashboard.inventory.models import Site

@pytest.mark.django_db
def test_create_circuit_provider():
    provider = CircuitProvider.objects.create(name='Windstream', email_folder='windstream_folder')
    assert provider.name == 'Windstream'
    assert provider.function_name == 'process_windstream'

@pytest.mark.django_db
def test_create_circuit_with_tag_and_site():
    provider = CircuitProvider.objects.create(name='Zayo', email_folder='zayo_folder')
    tag = CircuitTag.objects.create(name='Core-Alt')
    site = Site.objects.create(name='Test Site', address='123 Test Ln', city='Atlanta', state='GA', zip='30033')
    circuit = Circuit.objects.create(name='Zayo Circuit', cktid='ZAYO/001', provider=provider, site=site)
    circuit.tag.add(tag)
    assert circuit.tag.count() == 1
    assert str(circuit) == 'Zayo Circuit'