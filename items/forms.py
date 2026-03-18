from django import forms
from .models import LostItem, FoundItem, ItemMatch

class LostItemForm(forms.ModelForm):
    class Meta:
        model = LostItem
        fields = [
            'title', 'description', 'category', 'location_lost', 'location_detail',
            'date_lost', 'image', 'proof_of_ownership',
            'contact_email', 'contact_phone', 'reward',
            'verif_color', 'verif_distinguishing', 'verif_secret',
        ]
        widgets = {
            'date_lost': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_detail': forms.TextInput(attrs={'placeholder': 'e.g. Near window seat, Row 3'}),
            'verif_color': forms.TextInput(attrs={'placeholder': 'e.g. Matte black with red case, Samsung logo visible'}),
            'verif_distinguishing': forms.TextInput(attrs={'placeholder': 'e.g. Small crack on bottom-left corner, blue sticker on back'}),
            'verif_secret': forms.TextInput(attrs={'placeholder': 'e.g. Lock screen photo is a cat, inside pocket has a folded receipt'}),
        }
        labels = {
            'verif_color': '🔒 Colour / Appearance (private — for verification only)',
            'verif_distinguishing': '🔒 Distinguishing Features (private)',
            'verif_secret': '🔒 Secret Detail Only You Would Know (private)',
            'proof_of_ownership': '📎 Proof of Ownership (photo, receipt, etc.)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
        # Mark verification fields as not required but strongly encouraged
        self.fields['verif_color'].required = False
        self.fields['verif_distinguishing'].required = False
        self.fields['verif_secret'].required = False
        self.fields['proof_of_ownership'].required = False


class FoundItemForm(forms.ModelForm):
    class Meta:
        model = FoundItem
        fields = [
            'title', 'public_description', 'private_description',
            'category', 'location_found', 'location_detail',
            'date_found', 'image', 'contact_email', 'contact_phone', 'current_holding',
            'verif_color', 'verif_distinguishing', 'verif_secret',
        ]
        widgets = {
            'date_found': forms.DateInput(attrs={'type': 'date'}),
            'public_description': forms.Textarea(attrs={'rows': 3,
                'placeholder': 'Vague description for public listing e.g. "A black electronic device was found near the library"'}),
            'private_description': forms.Textarea(attrs={'rows': 3,
                'placeholder': 'Full confidential details e.g. "Black Samsung Galaxy S21, cracked screen bottom-left, found on desk Row 3 near window"'}),
            'location_detail': forms.TextInput(attrs={'placeholder': 'Exact spot — kept private'}),
            'current_holding': forms.TextInput(attrs={'placeholder': 'e.g. Security Office, Room 204 — kept private'}),
            'verif_color': forms.TextInput(attrs={'placeholder': 'Exact colour and appearance as you found it'}),
            'verif_distinguishing': forms.TextInput(attrs={'placeholder': 'Any scratches, stickers, or unique marks you noticed'}),
            'verif_secret': forms.TextInput(attrs={'placeholder': 'Any detail not visible from outside e.g. item inside a bag, note tucked in pocket'}),
        }
        labels = {
            'public_description': '🌐 Public Description (shown to everyone — keep vague)',
            'private_description': '🔒 Private Description (admin & verified owner only)',
            'location_detail': '🔒 Exact Location (private)',
            'current_holding': '🔒 Current Holding Location (private)',
            'verif_color': '🔒 Colour / Appearance (private)',
            'verif_distinguishing': '🔒 Distinguishing Features (private)',
            'verif_secret': '🔒 Additional Private Detail',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['verif_color'].required = False
        self.fields['verif_distinguishing'].required = False
        self.fields['verif_secret'].required = False


class MatchVerificationForm(forms.ModelForm):
    class Meta:
        model = ItemMatch
        fields = [
            'notes', 'admin_verif_notes',
            'verif_color_match', 'verif_distinguishing_match', 'verif_secret_match',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'admin_verif_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control',
                'placeholder': 'Document your verification findings here...'}),
        }
        labels = {
            'verif_color_match': 'Colour/appearance answers match?',
            'verif_distinguishing_match': 'Distinguishing feature answers match?',
            'verif_secret_match': 'Secret detail answers match?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif not isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'
        self.fields['verif_color_match'].required = False
        self.fields['verif_distinguishing_match'].required = False
        self.fields['verif_secret_match'].required = False


class ItemSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Search items...'}))
    category = forms.ChoiceField(required=False,
        choices=[('', 'All Categories')] + LostItem._meta.get_field('category').choices,
        widget=forms.Select(attrs={'class': 'form-select'}))
    location = forms.ChoiceField(required=False,
        choices=[('', 'All Locations')] + LostItem._meta.get_field('location_lost').choices,
        widget=forms.Select(attrs={'class': 'form-select'}))
