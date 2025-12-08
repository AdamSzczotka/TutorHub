from django import forms

from apps.accounts.models import User
from apps.rooms.models import Room
from apps.subjects.models import Level, Subject

from .models import Lesson
from .services import CalendarService


class LessonForm(forms.ModelForm):
    """Form for creating and editing lessons."""

    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='student', is_active=True),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox checkbox-sm'}),
        label='Uczniowie',
        error_messages={'required': 'Musisz wybrac przynajmniej jednego ucznia.'},
    )

    class Meta:
        model = Lesson
        fields = [
            'title',
            'description',
            'subject',
            'level',
            'tutor',
            'room',
            'start_time',
            'end_time',
            'is_group_lesson',
            'max_participants',
            'color',
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'placeholder': 'np. Matematyka - funkcje',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'textarea textarea-bordered w-full',
                    'rows': 2,
                    'placeholder': 'Dodatkowe informacje...',
                }
            ),
            'subject': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'level': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'tutor': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'room': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_time': forms.DateTimeInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'datetime-local',
                },
                format='%Y-%m-%dT%H:%M',
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'datetime-local',
                },
                format='%Y-%m-%dT%H:%M',
            ),
            'is_group_lesson': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'max_participants': forms.NumberInput(
                attrs={
                    'class': 'input input-bordered w-full max-w-xs',
                    'min': 2,
                    'max': 20,
                }
            ),
            'color': forms.TextInput(
                attrs={
                    'class': 'input input-bordered h-10 w-20',
                    'type': 'color',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set querysets for related fields
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        self.fields['level'].queryset = Level.objects.all().order_by('order_index')
        self.fields['tutor'].queryset = User.objects.filter(
            role='tutor', is_active=True
        )
        self.fields['room'].queryset = Room.objects.filter(is_active=True)
        self.fields['room'].required = False

        # Add empty option labels
        self.fields['subject'].empty_label = 'Wybierz przedmiot'
        self.fields['level'].empty_label = 'Wybierz poziom'
        self.fields['tutor'].empty_label = 'Wybierz korepetytora'
        self.fields['room'].empty_label = 'Online / bez sali'

        # If editing, get current students
        if self.instance.pk:
            self.fields['students'].initial = User.objects.filter(
                student_lessons__lesson=self.instance
            )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        tutor = cleaned_data.get('tutor')
        room = cleaned_data.get('room')
        is_group_lesson = cleaned_data.get('is_group_lesson')
        max_participants = cleaned_data.get('max_participants')
        students = cleaned_data.get('students')

        # Validate required tutor
        if not tutor:
            raise forms.ValidationError('Musisz wybrac korepetytora.')

        # Validate at least one student
        if not students or len(students) == 0:
            raise forms.ValidationError(
                'Musisz wybrac przynajmniej jednego ucznia.'
            )

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                'Czas zakończenia musi być po czasie rozpoczęcia.'
            )

        if is_group_lesson and not max_participants:
            raise forms.ValidationError(
                'Lekcja grupowa wymaga określenia maksymalnej liczby uczestników.'
            )

        # Check for conflicts
        if start_time and end_time and tutor:
            calendar_service = CalendarService()
            exclude_id = self.instance.pk if self.instance else None

            conflicts = calendar_service.check_conflicts(
                tutor_id=tutor.id,
                room_id=room.id if room else None,
                start_time=start_time,
                end_time=end_time,
                exclude_lesson_id=exclude_id,
            )

            if conflicts:
                conflict_titles = [c.title for c in conflicts]
                raise forms.ValidationError(
                    f'Konflikt z zajęciami: {", ".join(conflict_titles)}'
                )

        return cleaned_data
