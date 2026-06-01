from django import forms
from .models import ConsultationRequest, Document
from accounts.models import User
 
class ConsultationRequestForm(forms.ModelForm):
    class Meta:
        model = ConsultationRequest
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class ConsultationResponseForm(forms.ModelForm):
    class Meta:
        model = ConsultationRequest
        fields = ['resolution']
        widgets = {
            'resolution': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'document_type', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TeacherNotificationForm(forms.Form):
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    send_to_all = forms.BooleanField(required=False, initial=True, 
                                     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    selected_students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Estudiantes específicos (si no es a todos)'
    )

    def __init__(self, teacher, *args, **kwargs):
        super().__init__(*args, **kwargs)
        students = User.objects.filter(assigned_teachers__teacher=teacher, assigned_teachers__is_active=True)
        self.fields['selected_students'].queryset = students

class TeacherDocumentUploadForm(DocumentUploadForm):
    send_to_all = forms.BooleanField(required=False, initial=True, 
                                     label="Enviar a todos mis estudiantes",
                                     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    selected_students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Estudiantes específicos (si no es a todos)'
    )

    def __init__(self, teacher, *args, **kwargs):
        super().__init__(*args, **kwargs)
        students = User.objects.filter(assigned_teachers__teacher=teacher, assigned_teachers__is_active=True)
        self.fields['selected_students'].queryset = students