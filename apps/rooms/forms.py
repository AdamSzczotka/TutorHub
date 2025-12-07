from django import forms

from .models import Room


class RoomForm(forms.ModelForm):
    """Form for creating and editing rooms."""

    class Meta:
        model = Room
        fields = ['name', 'capacity', 'location', 'description', 'equipment', 'is_active', 'is_virtual']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwa sali',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 1,
                'placeholder': 'Liczba miejsc',
            }),
            'location': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Pietro 1, Pokoj 101',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Dodatkowy opis sali',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
            'is_virtual': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-secondary',
            }),
        }

    equipment_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Wyposazenie (jedno na linie)',
        }),
        label='Wyposazenie',
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with equipment as text."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            equipment = self.instance.equipment or {}
            items = equipment.get('items', [])
            self.fields['equipment_text'].initial = '\n'.join(items)
        # Remove original equipment field from visible fields
        self.fields['equipment'].widget = forms.HiddenInput()

    def clean(self):
        """Process equipment text into JSON."""
        cleaned_data = super().clean()
        equipment_text = cleaned_data.get('equipment_text', '')
        items = [line.strip() for line in equipment_text.split('\n') if line.strip()]
        cleaned_data['equipment'] = {'items': items}
        return cleaned_data
