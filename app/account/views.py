from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from django.views import generic

from account.forms import RegistrationForm
from building.models import Town


class SignUpView(generic.CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("home")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        Town.create(user=self.object)

        # login the user
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(self.request, user)
        return response

