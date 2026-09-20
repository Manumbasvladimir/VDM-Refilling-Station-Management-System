from django import forms

from accounts.models import User
from .models import Delivery


class AssignRiderForm(forms.ModelForm):

    rider = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.STAFF),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Assign Rider",
    )

    class Meta:
        model = Delivery
        fields = ["rider"]