from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from interlab.views import CustomFormView
from .models import Post

class PostListView(ListView):
    model = Post
    ordering = ['-created_at']
    paginate_by = 20
    context_object_name = 'posts'

class PostCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView, CustomFormView):
    model = Post
    fields = ['img', 'title', 'url', 'profile']
    success_url = reverse_lazy('post_list')

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(PostCreateView, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['profile'] = self.request.user.profile
        return initial
    
    def get_success_message(self, cleaned_data):
        success_message = _("Thanks ! Post was created successfully.")
        if not self.request.user.profile.public_contact_plateform:
            success_message += " " + _('Complete your <a href="/accounts/profile/edit/">public profile</a> to allow other users to contact you')
        
        return mark_safe(success_message)

class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')

class PostUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView, CustomFormView):
    model = Post
    fields = ['img', 'title', 'url', 'profile']
    success_url = reverse_lazy('post_list')

    def get_success_message(self, cleaned_data):
        success_message = _("Thanks ! Post was updated successfully.")
        if not self.request.user.profile.public_contact_plateform:
            success_message += " " + _('Complete your <a href="/accounts/profile/edit/">public profile</a> to allow other users to contact you')
        
        return mark_safe(success_message)
    