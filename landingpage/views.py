from django.shortcuts import render, redirect
from django.contrib import messages
from customer_service.models import CustomerReachout

def home(request):
    return render(request, "landingpage/page/home.html")


def contact(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        email = request.POST.get('email', '').strip()
        project_topic = request.POST.get('project_topic', '').strip()
        message = request.POST.get('message', '').strip()

        if fullname and email and message:
            CustomerReachout.objects.create(
                fullname=fullname,
                email=email,
                project_topic=project_topic,
                message=message
            )
            messages.success(request, "Thanks for reaching out! We'll get back to you soon.")
            return redirect('landingpage:home')
        else:
            messages.error(request, "Please fill in all fields.")
            

    return render(request, 'landing/page/home.html')