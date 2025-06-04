from django import forms

class AmountForm(forms.Form):
    amount = forms.DecimalField(
        label="Amount",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
    )
