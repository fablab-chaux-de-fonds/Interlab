from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy

from interlab.views import CustomFormView
from .models import Post

class PostListView(ListView):
    model = Post
    ordering = ['-created_at']
    paginate_by = 20
    context_object_name = 'posts'

    def get_template_names(self):
        if self.request.htmx:
            return 'share/post_list_items.html'
        return 'share/post_list.html'

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
    