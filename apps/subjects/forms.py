from django import forms

from .models import Level, Subject


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects."""

    class Meta:
        model = Subject
        fields = ['name', 'description', 'icon', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwa przedmiotu',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Opis przedmiotu',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. calculator, book, flask',
            }),
            'color': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'color',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class LevelForm(forms.ModelForm):
    """Form for creating and editing education levels."""

    class Meta:
        model = Level
        fields = ['name', 'description', 'order_index', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwa poziomu',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Opis poziomu',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'color': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'color',
            }),
        }
