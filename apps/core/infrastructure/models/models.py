import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count, Sum
from django.contrib.auth.models import User
from django.utils import timezone


class ActiveAreaManager(models.Manager):
    """Custom manager that returns only active areas."""
    def get_queryset(self):
        return super().get_queryset().filter(status='active')


class ActiveSpecialtyManager(models.Manager):
    """Custom manager that returns only active (not archived) specialties."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class ActiveDocumentManager(models.Manager):
    """Custom manager that returns only active (not archived) documents."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class ActiveClientManager(models.Manager):
    """Custom manager that returns only active clients."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Area(models.Model):
    """Organizational area model representing departments or divisions."""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#00bcd4')
    icon = models.CharField(max_length=50, default='fa-building')
    status = models.CharField(max_length=20, choices=[('active', 'Activa'), ('inactive', 'Inactiva')], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveAreaManager()

    class Meta:
        ordering = ['code']
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'

    def __str__(self):
        return f'{self.code} - {self.name}'


class Specialty(models.Model):
    """Professional specialty/skill category for team members.

    Hierarchical: a Specialty can have a parent (e.g. "Backend Developer"
    belongs to "Desarrollo"). The `parent` field is optional; top-level
    categories have parent=None.
    """
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('development', 'Desarrollo'), ('design', 'Diseño'), ('data', 'Datos'),
        ('devops', 'DevOps'), ('management', 'Gestión'), ('marketing', 'Marketing'),
        ('support', 'Soporte'), ('qa', 'Testing/QA'), ('other', 'Otro'),
    ])
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', help_text='Categoría padre (jerarquía)',
    )
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#00bcd4')
    icon = models.CharField(max_length=50, default='fa-code', blank=True)
    is_active = models.BooleanField(default=True, help_text='False = archivada (soft delete)')

    objects = models.Manager()
    active = ActiveSpecialtyManager()

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.name

    @property
    def is_root(self):
        return self.parent_id is None

    @property
    def full_path(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name


class Technology(models.Model):
    """Specific technology required by the company.

    The company pre-defines the tech stack it needs (e.g. "Python", "Django",
    "React", "PostgreSQL"). When a candidate applies, they mark which
    technologies they already know and at what level.
    """
    LEVEL_CHOICES = [
        (1, 'Básico'), (2, 'Intermedio'), (3, 'Avanzado'), (4, 'Experto'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('language', 'Lenguaje'), ('framework', 'Framework'),
        ('database', 'Base de datos'), ('tool', 'Herramienta'),
        ('platform', 'Plataforma'), ('other', 'Otro'),
    ], default='other')
    icon = models.CharField(max_length=50, default='fa-cog', blank=True)
    color = models.CharField(max_length=7, default='#64748b')
    is_active = models.BooleanField(default=True, help_text='La empresa sigue requiriéndola')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Tecnología'
        verbose_name_plural = 'Tecnologías'

    def __str__(self):
        return self.name


class CandidateProfile(models.Model):
    """Profile of a pending candidate, attached to a User created via
    self-registration. Holds CV, headline, bio and a list of technologies
    the candidate claims to know, each with a self-assessed level.

    Once the admin approves the user, this data is read by the admin to
    decide which role, area and specialty to assign. The admin does NOT
    have to mark technologies for the candidate — the candidate does it
    during the wizard registration.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='candidate_profile',
    )
    headline = models.CharField(
        max_length=200, blank=True,
        help_text='Ej: "Backend Developer con 3 años en Django"',
    )
    bio = models.TextField(blank=True, help_text='Resumen profesional')
    years_experience = models.PositiveSmallIntegerField(default=0)
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    cv_file = models.FileField(
        upload_to='cvs/%Y/%m/', null=True, blank=True,
        help_text='PDF, DOC o DOCX. Máx 5MB.',
    )
    technologies = models.ManyToManyField(
        Technology, through='CandidateTechnology',
        related_name='candidates', blank=True,
    )
    primary_specialty = models.ForeignKey(
        Specialty, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='primary_candidates',
        help_text='Especialidad principal que el candidato declara',
    )
    secondary_specialties = models.ManyToManyField(
        Specialty, blank=True, related_name='secondary_candidates',
        help_text='Otras especialidades que también maneja',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='candidates_reviewed',
    )
    review_notes = models.TextField(blank=True)
    review_checklist = models.JSONField(
        default=dict, blank=True,
        help_text='Checks de validacion del CV marcados manualmente por el revisor. Claves: cv_coherente, experiencia, tecnologias, documentacion.',
    )
    checklist_completed_at = models.DateTimeField(null=True, blank=True)
    checklist_score = models.PositiveSmallIntegerField(
        default=0,
        help_text='Checks marcados como validados (0-4)',
    )

    class Meta:
        verbose_name = 'Perfil de Candidato'
        verbose_name_plural = 'Perfiles de Candidatos'

    def __str__(self):
        return f'Candidato: {self.user.get_full_name() or self.user.email}'

    @property
    def cv_filename(self):
        return self.cv_file.name.split('/')[-1] if self.cv_file else None


class CandidateTechnology(models.Model):
    """Through-model that pairs a candidate with a technology and a level.

    The candidate self-assesses the level during the wizard. The admin can
    later override it but typically trusts the candidate's input.
    """
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(
        choices=Technology.LEVEL_CHOICES, default=2,
    )
    years_using = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('candidate', 'technology')
        verbose_name = 'Tecnología del candidato'
        verbose_name_plural = 'Tecnologías del candidato'

    def __str__(self):
        return f'{self.candidate.user} - {self.technology} ({self.get_level_display()})'


class UserProfile(models.Model):
    """Extended profile for User with role, area, specialty, and status information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True, related_name='practitioners')
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='portal_users')
    role = models.CharField(max_length=20, choices=[
        ('super-admin', 'Super Admin'), ('admin', 'Admin'),
        ('jefe-area', 'Jefe de Area'), ('jefe-proyecto', 'Jefe de Proyecto'),
        ('miembro', 'Miembro'),
        ('cliente', 'Cliente'), ('observer', 'Observador'),
    ], default='miembro', db_index=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente de aprobacion'), ('active', 'Activo'), ('vacation', 'Vacaciones'),
        ('leave', 'Licencia'), ('dismissed', 'Desactivado'), ('rejected', 'Rechazado'),
    ], default='pending', db_index=True)
    color = models.CharField(max_length=7, default='#00bcd4')
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.email} ({self.get_role_display()})'

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.email
        return ''.join(n[0].upper() for n in name.split()[:2])

    # Reglas de integridad segun rol (validadas en full_clean() y forms)
    ROLES_REQUIRING_AREA = ('miembro', 'jefe-area', 'jefe-proyecto')
    ROLES_REQUIRING_CLIENT = ('cliente',)
    ROLES_FORBIDDING_AREA = ('cliente',)
    ROLES_FORBIDDING_CLIENT = (
        'super-admin', 'admin', 'jefe-area', 'jefe-proyecto', 'miembro', 'observer',
    )

    def clean(self):
        super().clean()
        errors = {}

        if self.role in self.ROLES_REQUIRING_AREA and not self.area_id:
            errors['area'] = (
                f'Un usuario con rol "{self.get_role_display()}" debe pertenecer a un area.'
            )

        if self.role in self.ROLES_FORBIDDING_AREA and self.area_id:
            errors['area'] = (
                f'Un usuario con rol "{self.get_role_display()}" no debe tener un area asignada.'
            )

        if self.role in self.ROLES_REQUIRING_CLIENT and not self.client_id:
            errors['client'] = (
                f'Un usuario con rol "{self.get_role_display()}" debe estar asociado a una empresa.'
            )

        if self.role in self.ROLES_FORBIDDING_CLIENT and self.client_id:
            errors['client'] = (
                f'Un usuario con rol "{self.get_role_display()}" no debe estar asociado a una empresa.'
            )

        if errors:
            raise ValidationError(errors)


class Substitution(models.Model):
    """Represents a temporary substitution where one user covers for another."""
    original_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='substitutions')
    substitute_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='substituting')
    start_date = models.DateField()
    end_date = models.DateField()
    scope = models.CharField(max_length=20, choices=[
        ('all', 'Todo'), ('area', 'Solo Area'), ('projects', 'Solo Proyectos'),
    ], default='all')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Suplencia'
        verbose_name_plural = 'Suplencias'

    def __str__(self):
        return f'{self.substitute_user} suple a {self.original_user}'

    @property
    def is_current(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.active and self.start_date <= today <= self.end_date


def get_active_substitutions(user=None):
    """Return active substitutions for a given user or all active ones."""
    from django.utils import timezone
    today = timezone.now().date()
    qs = Substitution.objects.select_related('original_user', 'substitute_user')
    if user:
        qs = qs.filter(original_user=user)
    return qs.filter(active=True, start_date__lte=today, end_date__gte=today)


def get_substitute_for(user):
    """Return the active substitute user for a given user, or None."""
    sub = get_active_substitutions(user).first()
    return sub.substitute_user if sub else None


def get_substituting_for(user):
    """Return list of users that this user is currently substituting for."""
    subs = Substitution.objects.filter(
        substitute_user=user, active=True,
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).select_related('original_user')
    return [s.original_user for s in subs]


class Client(models.Model):
    """Client/customer model for project association."""
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, help_text='False = archivado (soft delete)')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveClientManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    """Project model representing a Scrum project with tasks, sprints, and team members."""
    name = models.CharField(max_length=200)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, related_name='projects')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Activo'), ('planned', 'Planificado'),
        ('completed', 'Completado'), ('paused', 'Pausado'),
        ('cancelled', 'Cancelado'),
    ], default='planned', db_index=True)
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_projects')
    members = models.ManyToManyField(User, blank=True, related_name='projects')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=7, default='#00bcd4')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status='done').count()
        return round((done / total) * 100)


class Sprint(models.Model):
    """Sprint model representing a time-boxed iteration in a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    goal = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planificado'), ('active', 'Activo'), ('completed', 'Completado'),
    ], default='planned', db_index=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.name} ({self.project.name})'


class Tag(models.Model):
    """Tag model for categorizing tasks with colored labels."""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#64748b')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskManager(models.Manager):
    """Custom manager for Task with optimized queries and common filters."""
    def get_queryset(self):
        return super().get_queryset().select_related('assignee', 'project', 'sprint').prefetch_related('tags')

    def by_status(self, status):
        return self.filter(status=status)

    def by_priority(self, priority):
        return self.filter(priority=priority)

    def by_assignee(self, user):
        return self.filter(assignee=user)

    def by_project(self, project):
        return self.filter(project=project)

    def active(self):
        return self.filter(status__in=['todo', 'in-progress'])

    def overdue(self):
        return self.filter(status__in=['todo', 'in-progress'], sprint__end_date__lt=timezone.now().date())

    def with_progress(self):
        return self.annotate(
            comment_count=Count('comments'),
            time_logged=Count('time_entries'),
        )


class Task(models.Model):
    """Task model representing a unit of work in a project (story, task, bug, epic)."""
    TYPE_CHOICES = [
        ('story', 'Historia'), ('task', 'Tarea'), ('bug', 'Bug'), ('epic', 'Epic'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'Alta'), ('medium', 'Media'), ('low', 'Baja'),
    ]
    STATUS_CHOICES = [
        ('backlog', 'Backlog'), ('todo', 'Por Hacer'),
        ('in-progress', 'En Progreso'), ('done', 'Completado'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=300)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    points = models.PositiveIntegerField(default=1)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    required_specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog', db_index=True)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    tasks = TaskManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment model for task and project discussions."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_files/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        target = self.task or self.project
        return f'Comment by {self.author} on {target}'


class Document(models.Model):
    """Document model for project file attachments with type detection."""
    TYPE_CHOICES = [
        ('pdf', 'PDF'), ('excel', 'Excel'), ('word', 'Word'),
        ('image', 'Imagen'), ('other', 'Otro'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=300)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    file = models.FileField(upload_to='documents/%Y/%m/', blank=True)
    size = models.PositiveIntegerField(default=0, help_text='Size in bytes')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True, help_text='False = archivado (soft delete)')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = ActiveDocumentManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def soft_delete(self):
        from django.utils import timezone
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at'])


class ServiceRequest(models.Model):
    """Service request model for IT service management (help desk, consulting, etc.)."""
    STATUS_CHOICES = [
        ('new', 'Nuevo'), ('reviewing', 'En Revision'),
        ('in-progress', 'En Progreso'), ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    SERVICE_CHOICES = [
        ('consultoria', 'Consultoria TI'), ('mesa-ayuda', 'Mesa de Ayuda TI'),
        ('remoto', 'Trabajo Remoto'), ('cloud', 'Cloud Computing'),
        ('capacitacion', 'Learning Center'), ('seguridad', 'Seguridad Informatica'),
        ('web', 'Paginas Web y E-commerce'), ('hosting', 'Hosting y VPS'),
        ('camaras', 'Camara de Videovigilancia'), ('soporte', 'Soporte Tecnico'),
        ('marketing', 'Marketing Digital'), ('community', 'Community Manager'),
        ('desarrollo', 'Desarrollo de Software'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='service_requests', null=True)
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client.name} - {self.get_service_display()}'


class TimeEntry(models.Model):
    """Time entry model for tracking hours spent on tasks."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=1)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user} - {self.task} ({self.hours}h)'


class Notification(models.Model):
    """Notification model for user alerts and system messages."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False, db_index=True)
    icon = models.CharField(max_length=50, default='fa-bell')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user})'


class AuditLog(models.Model):
    """Audit log model for tracking system-wide actions and changes."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f'{self.action} - {self.entity} by {self.user}'


class Message(models.Model):
    """Private message model for direct user-to-user communication."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f'{self.sender} -> {self.receiver}: {self.subject}'


class RegistrationRequest(models.Model):
    """Solicitud de registro pendiente de verificación por email.

    Guarda los datos del wizard de registro mientras el usuario confirma
    su email. El token es un UUID v4 que se envía por email como enlace.
    """
    token = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField()
    data = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cv_file = models.FileField(upload_to='cv_temp/%Y/%m/', null=True, blank=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pendiente'), ('verified', 'Verificado'), ('expired', 'Expirado')],
        default='pending',
        db_index=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Registro'
        verbose_name_plural = 'Solicitudes de Registro'

    def __str__(self):
        return f'{self.email} ({self.status})'
