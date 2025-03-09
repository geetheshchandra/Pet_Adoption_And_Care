from django import forms
from .models import Owner,Employee,AvailablePet

class OwnerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['user_name', 'pw', 'owner_name', 'email_id', 'phone_no', 'city', 'address']
        widgets = {
            'pw': forms.PasswordInput(),
        }

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['emp_name', 'salary', 'contact_no', 'job_role']

class AvailablePetForm(forms.ModelForm):
    class Meta:
        model = AvailablePet
        fields = ['species', 'breed', 'price', 'branch', 'status']