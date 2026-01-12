from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404
from .models import MyFile
from .forms import MyFileForm
from django.shortcuts import redirect


def home(request):
    return render(request, "pages/home.html")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    uploads = MyFile.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "pages/dashboard.html",
        {
            "uploads": uploads,
        },
    )


@login_required
def upload_file(request):
    if request.method == "POST":
        form = MyFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("file:dashboard")
    else:
        form = MyFileForm()

    return render(request, "pages/upload.html", {"form": form})


def layer_detail(request, pk):
    layer = get_object_or_404(MyFile, pk=pk)
    return render(request, "pages/detail.html", {"layer": layer})


# @login_required
# def home(request):
#     layers = MyFile.objects.all()
#     return render(request, "pages/home.html", {"layers": layers})
