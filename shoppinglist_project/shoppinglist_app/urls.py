from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),                # ✅ Home / Landing
    path('add/', views.add_item, name='add_item'),               # ✅ Add Item
    path('list/', views.item_list, name='item_list'),            # ✅ Item List
    path('edit/<int:item_id>/', views.edit_item, name='edit_item'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ocr-upload/', views.ocr_upload, name='ocr_view'),      # ✅ OCR page
    path('register/', views.register, name='register'),
    path('export-pdf/', views.export_pdf, name='item_pdf'),      # ✅ PDF Export
    path('mark/<int:item_id>/', views.mark_purchased, name='mark_purchased'),
    path('pending/<int:item_id>/', views.mark_pending, name='mark_pending'),
    path('ocr-result/', views.ocr_result, name='ocr_result'), # used for redirection
    path('add-item-ajax/', views.add_item_ajax, name='add_item_ajax'),
    path('ocr_uploaded_items/', views.view_ocr_uploads, name='ocr_uploaded_items')

]