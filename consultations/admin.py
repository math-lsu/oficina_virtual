from django.contrib import admin
from .models import TeacherAssignment, ConsultationRequest, Document, StudentDocumentStatus, Notification

class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'is_active', 'assigned_at')
    list_filter = ('is_active',)
    search_fields = ('student__username', 'teacher__username')
    raw_id_fields = ('student', 'teacher', 'assigned_by')

class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'teacher', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'student__username', 'teacher__username')

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'teacher', 'student', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'teacher__username', 'student__username')

class StudentDocumentStatusAdmin(admin.ModelAdmin):
    list_display = ('student', 'document', 'is_hidden')
    list_filter = ('is_hidden',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'verb')

# Registro explícito sin decoradores
admin.site.register(TeacherAssignment, TeacherAssignmentAdmin)
admin.site.register(ConsultationRequest, ConsultationRequestAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(StudentDocumentStatus, StudentDocumentStatusAdmin)
admin.site.register(Notification, NotificationAdmin)