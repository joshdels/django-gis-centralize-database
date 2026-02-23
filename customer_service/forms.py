from django import forms
from .models import CustomerMessage, CustomerReachout


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


class CustomerReachoutForm(forms.ModelForm):
    class Meta: 
        model = CustomerReachout
        fields = ['fullname', 'email', 'project_topic', 'message']
        widgets = {
            'fullname': forms.TextInput(attrs={'placeholder': 'Your full name', 'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your email', 'class': 'input input-bordered w-full'}),
            'project_topic': forms.TextInput(attrs={'placeholder': 'Project topic', 'class': 'input input-bordered w-full'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your message', 'class': 'textarea textarea-bordered w-full', 'rows': 5}),
        }