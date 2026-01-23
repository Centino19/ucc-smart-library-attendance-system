from django import forms
from .models import Patron


class PatronForm(forms.ModelForm):
    class Meta:
        model = Patron
        fields = ['id_number', 'first_name', 'middle_name', 'last_name','year_level', 'program', 'department', 'role']

        widgets = {
            # Force "type=text" here so dashes (-) are allowed
            'id_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'e.g. 2023-0001', 'type': 'text'}),

            'year_level': forms.Select(attrs={'class': 'form-select', 'id': 'id_year_level'}),

            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(Optional)'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'program': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BSCS'}),

        }