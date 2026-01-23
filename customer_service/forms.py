from django import forms
from .models import CustomerMessage


class CustomerMessageForm(forms.ModelForm):
    class Meta:
        model = CustomerMessage
        fields = [
            "subject",
            "category",
            "message",
        ]

        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Type your message here"}
            ),
            "subject": forms.TextInput(attrs={"placeholder": "Subject"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].required = True
        self.fields["message"].required = True


class CustomerMessageReplyForm(forms.ModelForm):
    class Meta:
        model = CustomerMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Type your reply here"}
            )
        }
