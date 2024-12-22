from django.shortcuts import render


# Create your views here.
def contact_us(request):
    return render(request, 'Home/website/contact.html')


def about_us(request):
    return render(request,'Home/website/about.html')