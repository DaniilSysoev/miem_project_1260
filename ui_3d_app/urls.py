from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='index')),
    path('index', views.index, name='index'),
    path('index/<int:printer_id>', views.index, name='index'),
    path('control', views.control, name='control'),
    path('control/<int:printer_id>', views.control, name='control'),
    path('camera', views.camera, name='camera'),
    path('camera/<int:printer_id>', views.camera, name='camera'),
    path('about', views.about, name='about'),
    path('new_printer', views.new_printer, name='new_printer'),
]
