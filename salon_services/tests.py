from django.test import TestCase
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage

from salon_services.models import Service


class ServiceCatalogTests(TestCase):
    def test_home_page_lists_services(self):
        Service.objects.create(
            name='Haircut',
            description='Classic haircut and styling',
            price='55.00',
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Haircut')
        self.assertContains(response, staticfiles_storage.url('images/services/haircut.jpg'))

    def test_service_list_uses_a_fallback_image(self):
        Service.objects.create(
            name='Manicure',
            description='Nail shaping and polish',
            price='30.00',
        )

        response = self.client.get(reverse('service_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, staticfiles_storage.url('images/services/manicure.jpg'))

# Create your tests here.
