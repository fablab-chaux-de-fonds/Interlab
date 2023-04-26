from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from accounts.models import CustomUser

# Create your tests here.
class TestOpeningSlotCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('fabcal:openingslot-create', args=['1681315200000', '1681322400000'])
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass',
            email='user@fake.django'
            )
        self.superuser = CustomUser.objects.create_user(
            username='testsuperuser',
            password='testpass',
            email='superuser@fake.django'
            )
        self.group = Group.objects.create(name='superuser')
        self.superuser.groups.add(self.group)

    def test_authenticated_user_can_access(self):
        self.client.login(username='testuser', password='testpass')

        # Test if user is not in superuser group
        self.assertFalse(self.user.groups.filter(name='superuser').exists())

        # Assert view-specific content
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)

        # Assert view-specific content
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_superuser_in_superuser_group(self):
        self.client.login(username='testsuperuser', password='testpass')
        # Test if user is in group
        self.assertTrue(self.superuser.groups.filter(name='superuser').exists())

        # Assert view-specific content
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.superuser.delete()
        self.group.delete()