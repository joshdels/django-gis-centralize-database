from django.shortcuts import render

def home(request):
    return render(request, "landingpage/page/home.html")


def contact(request):
    return render(request, "landingpage/page/contact.html")