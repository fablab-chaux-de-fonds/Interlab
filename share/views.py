from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy

from interlab.views import CustomFormView
from .models import Post

class PostListView(ListView):
    model = Post
    ordering = ['-created_at']
    paginate_by = 20
    context_object_name = 'posts'

class PostCreateView(LoginRequiredMixin, CreateView, CustomFormView):
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

class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')

class PostUpdateView(LoginRequiredMixin, UpdateView, CustomFormView):
    model = Post
    fields = ['img', 'title', 'url', 'profile']
    success_url = reverse_lazy('post_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    