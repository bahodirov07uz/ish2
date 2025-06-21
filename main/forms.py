from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import IshRequest

class IshRequestForm(forms.ModelForm):
    class Meta:
        model = IshRequest
        fields = ['mahsulot', 'soni', 'sana']

        widgets = {
            'sana': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'mahsulot': forms.Select(attrs={'class': 'form-control'}),
            'soni': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user and hasattr(self.user, 'ishchi_profile'):  
            instance.ishchi = self.user.ishchi_profile
        if commit:
            instance.save()
        return instance
    