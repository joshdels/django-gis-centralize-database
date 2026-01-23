from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required

from .models import CustomerMessage
from .forms import CustomerMessageForm, CustomerMessageReplyForm


def home(request):
    return HttpResponse("Hello dweb")


@login_required
def customer_chat(request):
    messages = CustomerMessage.objects.filter(
        parent__isnull=True, user=request.user
    ).order_by("created_at")

    if request.method == "POST":
        parent_id = request.POST.get("parent_id")
        if parent_id:
            form = CustomerMessageReplyForm(request.POST)
            parent_msg = CustomerMessage.objects.get(id=parent_id)
            if form.is_valid():
                msg = form.save(commit=False)
                
                if request.user.is_staff:
                    msg.sender = "STAFF"
                    msg.staff = request.user
                    msg.user = parent_msg.user 
                else: 
                    msg.sender = "USER"
                    msg.user = request.user
                    
                msg.parent = parent_msg
                parent_msg.status = "ONGOING"
                parent_msg.save()
                msg.save()
                return redirect("customer_service:chat")
        else:
            form = CustomerMessageForm(request.POST)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.user = request.user
                msg.sender = "USER"
                msg.save()
                return redirect("customer_service:chat")
    else:
        form = CustomerMessageForm()

    return render(
        request,
        "chat.html",
        {
            "form": form,
            "messages": messages,
            "reply_form": CustomerMessageReplyForm(),  # add for template
        },
    )


@login_required
def close_ticket(request, msg_id):
    msg = get_object_or_404(CustomerMessage, id=msg_id, user=request.user)
    msg.status = "CLOSED"
    msg.save()
    return redirect("customer_service:chat")
