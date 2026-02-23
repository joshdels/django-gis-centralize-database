from django.contrib import admin
from .models import CustomerMessage, CustomerReachout


class CustomerMessageInline(admin.TabularInline):
    model = CustomerMessage
    fk_name = "parent"
    extra = 1
    readonly_fields = ("user", "sender", "created_at")

    def save_new_instance(self, form, commit=True):
        """
        Helper to fill required fields when saving a new inline reply
        """
        obj = form.save(commit=False)
        obj.user = obj.parent.user
        obj.sender = "STAFF"
        obj.staff = form.current_user
        if commit:
            obj.save()
        return obj


class CustomerMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "staff", "category", "sender", "status", "created_at")
    list_filter = ("category", "status", "sender")
    search_fields = ("user__username", "staff__username", "message")
    inlines = [CustomerMessageInline]
    ordering = ("-created_at",)

    def save_formset(self, request, form, formset, change):
        """
        Override to assign staff and user for inline replies
        """
        if formset.model == CustomerMessage:
            for inline_form in formset.forms:
                if inline_form.cleaned_data and not inline_form.instance.pk:
                    inline_form.instance.user = inline_form.instance.parent.user
                    inline_form.instance.sender = "STAFF"
                    inline_form.instance.staff = request.user
        formset.save()


admin.site.register(CustomerMessage, CustomerMessageAdmin)
admin.site.register(CustomerReachout)
