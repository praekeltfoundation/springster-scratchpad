# -*- coding: utf-8 -*-
from datetime import date

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.test.client import Client
from molo.core.tests.base import MoloTestCaseMixin

from molo.profiles.models import UserProfile
from gem.admin import GemUserAdmin, download_as_csv_gem
from gem.models import GemUserProfile
from molo.profiles.task import send_export_email
from django.conf import settings
from django.core import mail
from gem.tasks import send_export_email_gem


class TestFrontendUsersAdminView(TestCase, MoloTestCaseMixin):
    def setUp(self):
        self.mk_main()
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='0000',
            is_staff=False)

        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='admin@example.com',
            password='0000',
            is_staff=True)

        self.client = Client()
        self.client.login(username='superuser', password='0000')

    def test_staff_users_are_not_shown(self):
        response = self.client.get(
            '/admin/auth/user/?usertype=frontend'
        )

        self.assertContains(response, self.user.username)
        self.assertNotContains(response, self.superuser.email)

    def test_export_csv(self):
        profile = self.user.profile
        profile.alias = 'The Alias'
        profile.date_of_birth = date(1985, 1, 1)
        profile.mobile_number = '+27784667723'
        profile.save()
        gem_profile = self.user.gem_profile
        gem_profile.gender = 'f'
        gem_profile.save()

        response = self.client.post('/admin/auth/user/')
        self.assertEquals(response.status_code, 302)

    def test_send_export_email(self):
        send_export_email_gem(self.user.email, {})
        message = list(mail.outbox)[0]
        self.assertEquals(message.to, [self.user.email])
        self.assertEquals(
            message.subject, 'Molo export: ' + settings.SITE_NAME)
        self.assertEquals(
            message.attachments[0],
            ('Molo_export_GEM.csv',
             'username,alias,first_name,last_name,date_of_birth,email,mobile_'
             'number,is_active,date_joined,last_login,gender\r\ntester,,,,,t'
             'ester@example.com,,1,' + str(
                 self.user.date_joined.strftime("%Y-%m-%d %H:%M:%S")) +
             ',,\r\n',
             'text/csv'))

    def test_export_csv_no_gem_profile(self):
        GemUserProfile.objects.all().delete()
        self.assertEquals(GemUserProfile.objects.all().count(), 0)

        response = self.client.post('/admin/auth/user/')
        self.assertEquals(response.status_code, 302)


class ModelsTestCase(TestCase, MoloTestCaseMixin):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='tester')
        self.mk_main()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_download_csv(self):
        profile = self.user.profile
        profile.alias = 'The Alias'
        profile.mobile_number = '+27784667723'
        profile.save()
        date = str(self.user.date_joined.strftime("%Y-%m-%d %H:%M"))
        gem_profile = self.user.gem_profile
        gem_profile.gender = 'f'
        gem_profile.date_of_birth = date
        gem_profile.save()
        response = download_as_csv_gem(GemUserAdmin(UserProfile, self.site),
                                       None,
                                       User.objects.all())
        expected_output = (
            'Content-Type: text/csv\r\nContent-Disposition: attachment;filen'
            'ame=export.csv\r\n\r\nusername,email,first_name,last_name,is_sta'
            'ff,date_joined,alias,mobile_number,date_of_birth,gender\r\nte'
            'ster,tester@example.com,,,False,' + date + ',The Alias,+277'
            '84667723,,f\r\n')
        self.assertEquals(str(response), expected_output)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_download_csv_no_gem_profile(self):
        gem_profile = self.user.gem_profile
        gem_profile.delete()
        response = download_as_csv_gem(GemUserAdmin(UserProfile, self.site),
                                       None,
                                       User.objects.all())
        expected_output = (
            'Content-Type: text/csv\r\nContent-Disposition: attachment;file'
            'name=export.csv\r\n\r\nusername,email,first_name,last_name,is_st'
            'aff,date_joined,alias,mobile_number,date_of_birth,gender\r\n')
        self.assertEquals(str(response), expected_output)
