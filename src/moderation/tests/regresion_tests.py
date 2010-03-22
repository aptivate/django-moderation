from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation import ModerationManager
from moderation.tests.test_app.models import UserProfile
from django.contrib.auth.models import User
from moderation.models import MODERATION_STATUS_APPROVED
import django


django_version = django.get_version()[:3]


class CSRFMiddlewareTestCase(SettingsTestCase):
    fixtures = ['test_users.json']
    urls = 'moderation.tests.test_urls'
    test_settings = 'moderation.tests.settings.csrf_middleware'
    
    def setUp(self):
        import moderation
        self.moderation = ModerationManager()
        self.moderation.register(UserProfile)

        self.old_moderation = moderation
        setattr(moderation, 'moderation', self.moderation)

    def tearDown(self):
        import moderation
        self.moderation.unregister(UserProfile)
        setattr(moderation, 'moderation', self.old_moderation)
        
    def test_csrf_token(self):
        profile = UserProfile(description='Profile for new user',
                    url='http://www.yahoo.com',
                    user=User.objects.get(username='user1'))

        profile.save()

        self.client.login(username='admin', password='aaaa')

        url = profile.moderated_object.get_admin_moderate_url()

        if django_version == '1.1':
            from django.contrib.csrf.middleware import _make_token
            csrf_token = _make_token(self.client.session.session_key)
            post_data = {'approve': 'Approve',
                         'csrfmiddlewaretoken': csrf_token}
        else:
            post_data = {'approve': 'Approve'}

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)

        profile = UserProfile.objects.get(pk=profile.pk)

        self.assertEqual(profile.moderated_object.moderation_status,
                         MODERATION_STATUS_APPROVED)
