import re
from django import forms
from django.forms import Form
from django.utils.translation import ugettext_lazy as _
from gem.constants import GENDERS
from gem.models import GemSettings
from molo.profiles.forms import RegistrationForm, EditProfileForm
from molo.profiles.models import UserProfile
from gem.settings import REGEX_EMAIL, REGEX_PHONE

from wagtail.wagtailcore.models import Site


def validate_no_email_or_phone(input):
    regexes = [REGEX_EMAIL, REGEX_PHONE]
    for regex in regexes:
        match = re.search(regex, input)
        if match:
            return False

    return True


class GemAliasMixin(object):

    def _clean_alias(self):
        """
        Check for email addresses, telephone numbers and any other keywords or
        patterns defined through GemSettings.
        """
        alias = self.cleaned_data['alias']

        if not validate_no_email_or_phone(alias):
            raise forms.ValidationError(
                _(
                    "Sorry, but that is an invalid display name. Please don't"
                    " use your email address or phone number in your display"
                    " name.")
            )

        site = Site.objects.get(is_default_site=True)
        settings = GemSettings.for_site(site)

        banned_list = [REGEX_EMAIL, REGEX_PHONE]

        banned_names_with_offensive_language = \
            settings.banned_names_with_offensive_language.split('\n') \
            if settings.banned_names_with_offensive_language else []

        banned_list += banned_names_with_offensive_language

        for keyword in banned_list:
            keyword = keyword.replace('\r', '')
            match = re.search(keyword, alias.lower())
            if match:
                raise forms.ValidationError(
                    _(
                        'Sorry, the name you have used is not allowed. '
                        'Please, use a different name for your display name.'
                    )
                )

        return alias


class GemRegistrationForm(GemAliasMixin, RegistrationForm):
    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=GENDERS,
        required=True
    )

    alias = forms.RegexField(
        regex=r'^[\w.@+-]+$',
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=30,
            )
        ),
        label=_("Display Name"),
        error_messages={
            'invalid': _("This value must contain only letters, "
                         "numbers and underscores."),
        }
    )

    security_question_1_answer = forms.CharField(
        label=_("Answer to Security Question 1"),
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=128,
            )
        ),
    )

    security_question_2_answer = forms.CharField(
        label=_("Answer to Security Question 2"),
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=128,
            )
        ),
    )

    def clean_username(self):
        username = super(GemRegistrationForm, self).clean_username()

        if not validate_no_email_or_phone(username):
            raise forms.ValidationError(
                _(
                    "Sorry, but that is an invalid username. Please don't use"
                    " your email address or phone number in your username."
                )
            )

        return username

    def clean_alias(self):
        return self._clean_alias()


class GemForgotPasswordForm(Form):
    username = forms.RegexField(
        regex=r'^[\w.@+-]+$',
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=30,
            )
        ),
        label=_("Username"),
        error_messages={
            'invalid': _("This value must contain only letters, "
                         "numbers and underscores."),
        }
    )

    random_security_question_answer = forms.CharField(
        label=_("Answer to Security Question"),
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=128,
            )
        ),
    )


class GemResetPasswordForm(Form):
    username = forms.CharField(
        widget=forms.HiddenInput()
    )

    token = forms.CharField(
        widget=forms.HiddenInput()
    )

    password = forms.RegexField(
        regex=r'^\d{4}$',
        widget=forms.PasswordInput(
            attrs=dict(
                required=True,
                render_value=False,
                type='password',
            )
        ),
        max_length=4,
        min_length=4,
        error_messages={
            'invalid': _("This value must contain only numbers."),
        },
        label=_("PIN")
    )

    confirm_password = forms.RegexField(
        regex=r'^\d{4}$',
        widget=forms.PasswordInput(
            attrs=dict(
                required=True,
                render_value=False,
                type='password',
            )
        ),
        max_length=4,
        min_length=4,
        error_messages={
            'invalid': _("This value must contain only numbers."),
        },
        label=_("Confirm PIN")
    )


class GemEditProfileForm(GemAliasMixin, EditProfileForm):
    alias = forms.RegexField(
        regex=r'^[\w.@+-]+$',
        widget=forms.TextInput(
            attrs=dict(
                required=True,
                max_length=30,
            )
        ),
        label=_("Display Name"),
        error_messages={
            'invalid': _("This value must contain only letters, "
                         "numbers and underscores."),
        }
    )

    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=GENDERS,
        required=False
    )

    def clean_alias(self):
        return self._clean_alias()

    class Meta:
        model = UserProfile
        fields = ['alias', 'date_of_birth', 'mobile_number', 'gender']


class ReportCommentForm(Form):
    CHOICES = (
        ('Spam', _('Spam')),
        ('Offensive Language', _('Offensive Language')),
        ('Bullying', _('Bullying')),
        ('Other', _('Other'))
    )

    report_reason = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=CHOICES
    )
