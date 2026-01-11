from django.shortcuts import render, redirect, get_object_or_404
from .models import MyFile
from .forms import MyFileForm


def base(request):
    layers = MyFile.objects.all()
    return render(request, "home.html", {"layers": layers})


def upload_file(request):
    if request.method == "POST":
        form = MyFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("file:home")

    else:
        form = MyFileForm()
    return render(request, "upload.html", {"form": form})


def layer_detail(request, pk):
    layer = get_object_or_404(MyFile, pk=pk)
    return render(request, "detail.html", {"layer": layer})
