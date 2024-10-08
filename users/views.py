import secrets

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView

from config.settings import EMAIL_HOST_USER
from users.forms import UserRegisterForm
from users.models import User
from users.utils import generate_password


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:email_confirm")

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="Ларёк - подтверждение Email",
            message=f"Привет, {user.email}! Для окончания регистрации в интернет-магазине Ларёк, перейди по ссылке - {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse("users:login"))


class EmailConfirmView(TemplateView):
    template_name = "users/email_confirm.html"


class UserPasswordResetView(PasswordResetView):
    model = User
    form_class = PasswordResetForm
    success_url = reverse_lazy("users:password_reset")

    def form_valid(self, form: User):
        if self.request.method == "POST":
            email = self.request.POST["email"]
            try:
                user = User.objects.get(email=email)
                password = generate_password(10)
                user.password = password
                user.set_password(password)
                user.save()
                send_mail(
                    subject="Ларёк - восстановление пароля",
                    message=f"Привет, {user.email}! Это твой новый пароль для входа в интернет-магазине Ларёк - {password}",
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[user.email],
                )
                return redirect(reverse("users:new_password"))
            except Exception:
                return redirect(reverse("users:email_not_found"))
        return super().form_valid(form)


class NewPasswordView(TemplateView):
    template_name = "users/new_password.html"


class EmailNotFoundView(TemplateView):
    template_name = "users/email_not_found.html"
