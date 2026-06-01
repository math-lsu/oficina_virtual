from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # Dashboards
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),

    # Consultation requests
    path('create/', views.CreateRequestView.as_view(), name='create_request'),
    path('<int:pk>/', views.ViewRequestDetailView.as_view(), name='view_request'),
    path('<int:pk>/respond/', views.RespondRequestView.as_view(), name='respond_request'),
    path('<int:request_pk>/upload/', views.UploadDocumentToRequestView.as_view(), name='upload_document_to_request'),

    # Documents (general upload by teacher)
    path('documents/upload/', views.UploadDocumentView.as_view(), name='upload_document'),
    path('documents/student/', views.StudentDocumentsView.as_view(), name='student_documents'),
    path('documents/exercises/', views.StudentExercisesView.as_view(), name='student_exercises'),
    path('documents/submit/<int:exercise_id>/', views.SubmitExerciseView.as_view(), name='submit_exercise'),
    path('documents/my-submissions/', views.MySubmissionsView.as_view(), name='my_submissions'),
    path('documents/review/', views.ReviewSubmissionsView.as_view(), name='review_submissions'),
    path('documents/download/<int:doc_id>/', views.DownloadDocumentView.as_view(), name='download_document'),
    path('documents/hide/<int:doc_id>/', views.HideDocumentView.as_view(), name='hide_document'),

    # Notifications
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('send-notification/', views.SendNotificationView.as_view(), name='send_notification'),
]