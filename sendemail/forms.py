from django import forms


class ContactForm(forms.Form):
    email = forms.EmailField(
        label="Your email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Your e-mail"}),
        error_messages={"required": "Enter your email !"}
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
        error_messages={"required": "Enter a subject !"}
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Your message"}),
        error_messages={"required": "Enter a message !"},
        min_length=20
    )
