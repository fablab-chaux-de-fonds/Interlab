from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from interlab.views import CustomFormView
from .models import Post

class PostListView(ListView):
    model = Post

class PostCreateView(LoginRequiredMixin, CreateView, CustomFormView):
    model = Post
    fields = ['img', 'title', 'profile']
    success_url = reverse_lazy('post_list')

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(PostCreateView, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['profile'] = self.request.user.profile
        return initial

    def is_valid(self):
        # Get the initial dictionary from the superclass method
        initial = super(PostCreateView, self).is_valid()
        pass

class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')