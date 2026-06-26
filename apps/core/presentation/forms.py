from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.core.infrastructure.models.models import (
    Area, Specialty, Technology, Client, Project, Sprint, Task,
    ServiceRequest, Substitution, UserProfile, Document
)


class AreaForm(forms.ModelForm):
    """Form for creating and editing organizational areas."""
    class Meta:
        model = Area
        fields = ['code', 'name', 'description', 'status']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: DEV, QA, OPS'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del area'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class SpecialtyForm(forms.ModelForm):
    """Form for creating and editing professional specialties."""
    class Meta:
        model = Specialty
        fields = ['name', 'category', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la especialidad'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ClientForm(forms.ModelForm):
    """Form for creating and editing clients."""
    class Meta:
        model = Client
        fields = ['name', 'contact', 'email', 'phone', 'industry']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@cliente.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 890'}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Industria'}),
        }


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects."""
    class Meta:
        model = Project
        fields = ['name', 'area', 'description', 'status', 'lead', 'client', 'budget', 'start_date', 'end_date', 'color', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proyecto'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].required = False
        self.fields['lead'].required = False
        self.fields['client'].required = False
        self.fields['budget'].required = False
        self.fields['budget'].initial = 0
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['members'].required = False
        self.fields['description'].required = False
        self.fields['description'].initial = ''
        self.fields['color'].required = False
        self.fields['color'].initial = '#00bcd4'


class SprintForm(forms.ModelForm):
    """Form for creating sprints."""
    class Meta:
        model = Sprint
        fields = ['project', 'name', 'start_date', 'end_date', 'goal']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del sprint'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'goal': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks."""
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3'}),
        help_text='Separar etiquetas con comas',
    )

    class Meta:
        model = Task
        fields = ['project', 'sprint', 'title', 'type', 'priority', 'points', 'assignee', 'required_specialty', 'status', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'sprint': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titulo de la tarea'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'required_specialty': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MemberForm(forms.ModelForm):
    """Form for creating and editing team members (UserProfile).

    Project assignment is intentionally NOT in this form. Admins edit the
    profile here; project assignment happens from the project's own
    'Members' view (can_assign_to_project) by the admin, jefe-area, or
    jefe-proyecto.
    """
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text='Dejar en blanco para no cambiar')
    password_confirm = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text='Repetir contrasena para confirmar (opcional)')

    client = forms.ModelChoiceField(
        queryset=Client.active.all(),
        required=False,
        empty_label='Sin cliente',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_client'}),
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'area', 'specialty', 'client', 'role', 'status', 'color']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-select', 'id': 'id_area'}),
            'specialty': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select', 'id': 'id_role'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        clients_qs = kwargs.pop('clients_qs', None)
        areas_qs = kwargs.pop('areas_qs', None)
        specialties_qs = kwargs.pop('specialties_qs', None)
        super().__init__(*args, **kwargs)

        if clients_qs is not None:
            self.fields['client'].queryset = clients_qs
        if areas_qs is not None:
            self.fields['area'].queryset = areas_qs
        if specialties_qs is not None:
            self.fields['specialty'].queryset = specialties_qs

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')

        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', 'Las contrasenas no coinciden')
            if password and len(password) < 6:
                self.add_error('password', 'La contrasena debe tener al menos 6 caracteres')

        # Aplica las reglas de integridad del modelo segun el rol:
        #   - miembro / jefe-area / jefe-proyecto requieren area
        #   - cliente requiere client y NO debe tener area
        if self.instance:
            for field in ('role', 'area', 'client', 'specialty', 'phone', 'color', 'status'):
                if field in cleaned and cleaned[field] is not None:
                    setattr(self.instance, field, cleaned[field])
            try:
                self.instance.clean()
            except ValidationError as e:
                for fname, msgs in e.message_dict.items():
                    for m in msgs:
                        self.add_error(fname if fname != '__all__' else None, m)

        return cleaned


class ServiceRequestForm(forms.ModelForm):
    """Form for creating and editing service requests."""
    class Meta:
        model = ServiceRequest
        fields = ['client', 'service', 'description', 'status', 'assigned_to']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }


class TechnologyForm(forms.ModelForm):
    """Form for creating and editing technologies."""
    class Meta:
        model = Technology
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la tecnologia'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class SubstitutionForm(forms.ModelForm):
    """Form for creating substitutions."""
    class Meta:
        model = Substitution
        fields = ['original_user', 'substitute_user', 'start_date', 'end_date', 'scope', 'reason']
        widgets = {
            'original_user': forms.Select(attrs={'class': 'form-select'}),
            'substitute_user': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scope': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
