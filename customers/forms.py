
from django import forms
from .models import CustomerProfile


class CustomerProfileForm(forms.ModelForm):

    class Meta:
        model = CustomerProfile

        fields = [
            "house_number",
            "street",
            "barangay",
            "municipality",
            "province",
            "zip_code",
            "landmark",
            "delivery_notes",
        ]

        widgets = {
            "house_number": forms.TextInput(attrs={"class": "form-control"}),
            "street": forms.TextInput(attrs={"class": "form-control"}),
            "barangay": forms.TextInput(attrs={"class": "form-control"}),
            "municipality": forms.TextInput(attrs={"class": "form-control"}),
            "province": forms.TextInput(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "landmark": forms.TextInput(attrs={"class": "form-control"}),
            "delivery_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }