from django.urls import path
from registry import views as v
urlpatterns=[
 path('branding/<str:kind>/',v.branding_image,name='branding_image'),
 path('reports/member/<int:member_id>/',v.member_report,name='member_report'),
 path('password/',v.password_change,name='password'),
 path('',v.dashboard,name='dashboard'),path('login/',v.login_view,name='login'),path('logout/',v.logout_view,name='logout'),
 path('members/',v.members,name='members'),path('members/new/',v.member_edit,name='member_new'),path('members/<int:pk>/',v.detail,name='detail'),path('members/<int:pk>/edit/',v.member_edit,name='member_edit'),path('members/<int:pk>/delete/',v.delete_license,name='delete_license'),
 path('members/<int:pk>/payment/',v.payment,name='payment'),path('members/<int:pk>/debt/',v.add_debt,name='add_debt'),path('members/<int:pk>/credit/<int:receipt_id>/',v.allocate_credit,name='allocate_credit'),
 path('members/<int:pk>/dues/<int:due_id>/discount/',v.add_discount,name='discount'),path('members/<int:pk>/dues/<int:due_id>/reopen/',v.reopen_due,name='reopen'),
 path('members/<int:pk>/upload/',v.upload_document,name='upload'),path('documents/<int:pk>/',v.document_file,name='document'),path('archive/',v.archive,name='archive'),
 path('finance/',v.finance,name='finance'),path('settings/',v.settings_view,name='settings'),path('users/',v.users_view,name='users'),path('audit/',v.audit_view,name='audit'),
 path('excel/',v.import_excel,name='excel'),path('export/',v.export_excel,name='export'),
]
