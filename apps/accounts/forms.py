"""Forms for accounts app."""

import secrets
import string

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import transaction

from apps.students.models import StudentProfile
from apps.tutors.models import TutorProfile

User = get_user_model()


phone_validator = RegexValidator(
    regex=r'^\+48\d{9}$',
    message='Numer telefonu musi być w formacie +48XXXXXXXXX',
)


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password.

    Args:
        length: Password length (default 12).

    Returns:
        Randomly generated password string.
    """
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class AdminUserCreationForm(forms.ModelForm):
    """Form for admin to create new users directly."""

    # Role selection
    role = forms.ChoiceField(
        choices=[
            ('student', 'Uczeń'),
            ('tutor', 'Korepetytor'),
            ('admin', 'Administrator'),
        ],
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label='Rola',
    )

    # Student-specific fields
    class_name = forms.CharField(
        max_length=10,
        required=False,
        label='Klasa',
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'np. 7A, 3LO',
        }),
    )
    parent_name = forms.CharField(
        max_length=100,
        required=False,
        label='Imię i nazwisko rodzica',
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
    )
    parent_email = forms.EmailField(
        required=False,
        label='Email rodzica',
        widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
    )
    parent_phone = forms.CharField(
        max_length=20,
        required=False,
        label='Telefon rodzica',
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '+48123456789',
        }),
    )

    # Tutor-specific fields
    education = forms.CharField(
        max_length=200,
        required=False,
        label='Wykształcenie',
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
    )
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=50,
        required=False,
        label='Lata doświadczenia',
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
    )
    hourly_rate = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        label='Stawka godzinowa (zł)',
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01',
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48123456789',
            }),
        }
        labels = {
            'email': 'Email',
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'phone': 'Telefon',
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        # Validate student-specific fields
        if role == 'student':
            if not cleaned_data.get('parent_email'):
                self.add_error('parent_email', 'Email rodzica jest wymagany dla ucznia.')

        return cleaned_data

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_validator(phone)
        return phone

    def clean_parent_phone(self):
        """Validate parent phone number format."""
        phone = self.cleaned_data.get('parent_phone')
        if phone:
            phone_validator(phone)
        return phone

    @transaction.atomic
    def save(self, commit: bool = True, created_by=None) -> tuple:
        """Save the user and create role-specific profile.

        Args:
            commit: Whether to save to database.
            created_by: Admin user who is creating this user.

        Returns:
            Tuple of (user, temp_password).
        """
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']

        # Generate temporary password
        temp_password = generate_temp_password()
        user.set_password(temp_password)
        user.first_login = True
        user.is_profile_completed = False

        if commit:
            user.save()

            # Create role-specific profile
            role = self.cleaned_data['role']

            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    class_name=self.cleaned_data.get('class_name', ''),
                    parent_name=self.cleaned_data.get('parent_name', ''),
                    parent_email=self.cleaned_data.get('parent_email', ''),
                    parent_phone=self.cleaned_data.get('parent_phone', ''),
                )

            elif role == 'tutor':
                TutorProfile.objects.create(
                    user=user,
                    education=self.cleaned_data.get('education', ''),
                    experience_years=self.cleaned_data.get('experience_years'),
                    hourly_rate=self.cleaned_data.get('hourly_rate'),
                )

            # Log creation
            if created_by:
                from apps.accounts.models import UserCreationLog
                UserCreationLog.objects.create(
                    created_user=user,
                    created_by=created_by,
                    email_sent=False,
                )

        return user, temp_password


class UserProfileForm(forms.ModelForm):
    """Form for users to update their profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48123456789',
            }),
            'avatar': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
        }
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'phone': 'Telefon',
            'avatar': 'Zdjęcie profilowe',
        }

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_validator(phone)
        return phone


class StudentProfileForm(forms.ModelForm):
    """Form for student-specific profile fields."""

    class Meta:
        model = StudentProfile
        fields = [
            'class_name', 'current_level', 'learning_goals',
            'parent_name', 'parent_phone', 'parent_email',
            'secondary_parent_name', 'secondary_parent_phone',
            'emergency_contact', 'notes',
        ]
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'current_level': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'learning_goals': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
            }),
            'parent_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'parent_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'parent_email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'secondary_parent_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'secondary_parent_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
            }),
        }
        labels = {
            'class_name': 'Klasa',
            'current_level': 'Aktualny poziom',
            'learning_goals': 'Cele nauki',
            'parent_name': 'Imię i nazwisko rodzica',
            'parent_phone': 'Telefon rodzica',
            'parent_email': 'Email rodzica',
            'secondary_parent_name': 'Imię drugiego rodzica',
            'secondary_parent_phone': 'Telefon drugiego rodzica',
            'emergency_contact': 'Kontakt awaryjny',
            'notes': 'Notatki',
        }


class TutorProfileForm(forms.ModelForm):
    """Form for tutor-specific profile fields."""

    class Meta:
        model = TutorProfile
        fields = [
            'bio', 'education', 'experience_years',
            'hourly_rate',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
            }),
            'education': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'experience_years': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
            }),
        }
        labels = {
            'bio': 'Opis',
            'education': 'Wykształcenie',
            'experience_years': 'Lata doświadczenia',
            'hourly_rate': 'Stawka godzinowa (zł)',
        }


class UserEditForm(forms.ModelForm):
    """Form for admin to edit user details."""

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48123456789',
            }),
            'role': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
        labels = {
            'email': 'Email',
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'phone': 'Telefon',
            'role': 'Rola',
            'is_active': 'Aktywny',
        }

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_validator(phone)
        return phone


class PasswordChangeForm(forms.Form):
    """Form for changing user password."""

    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='Nowe hasło',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='Potwierdź hasło',
    )

    def clean(self):
        """Validate passwords match."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'Hasła nie są takie same.')

        return cleaned_data
