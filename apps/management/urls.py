
from django.urls import path

from  .import views

urlpatterns = [

    path('books', views.books_in_store, name='books_in_store'),
    path('borrowed/books', views.borrowed_books, name='borrowed_books'),
    path('fines', views.book_fines, name='book_fines'),
    path('issue/<int:id>', views.issue_book, name='issue_book'),
    path('return/<int:id>', views.return_book, name='return_book'),
    path('pay/<int:id>',views.pay_overdue,name='pay_overdue'),
    path('handle/paymment/transactions<int:id>',views.callback,name='callback'),
    path('performance',views.grade_performance_view,name='grade_performance_view'),
    path('performance/<int:grade_id>/<int:term_id>/', views.grade_performance_view, name='grade_performance'),

    ]