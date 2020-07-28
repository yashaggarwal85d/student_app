from django.http import  HttpResponse, Http404,HttpResponseRedirect
from braces.views import SelectRelatedMixin
from . import forms
from . import models
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse,reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404,render,redirect
from django.views import generic
from projects.models import Project,ProjectMember
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


User = get_user_model()

class IssueList(SelectRelatedMixin, generic.ListView):
    model = models.Issue
    select_related = ("user", "project")


# class UserIssues(generic.ListView):
#     model = models.Issue
#     template_name = "issues/user_issue_list.html"

#     def get_queryset(self):
#         try:
#             self.issue_user = User.objects.prefetch_related("issues").get(
#                 username__iexact=self.kwargs.get("username")
#             )
#         except User.DoesNotExist:
#             raise Http404
#         else:
#             return self.issue_user.issues.all()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["issue_user"] = self.issue_user
#         return context



class CreateIssue(LoginRequiredMixin, SelectRelatedMixin,generic.CreateView):
    model = models.Issue
    form_class = forms.IssueForm
    template_name = 'issues/issue_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        form.save_m2m()
        return super().form_valid(form)
    

class DeleteIssue(LoginRequiredMixin, SelectRelatedMixin,generic.DeleteView):
    model = models.Issue
    select_related = ("user", "project")
    success_url = reverse_lazy("home")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user_id=self.request.user.id)

    def delete(self, *args, **kwargs):
        messages.success(self.request, "Issue Deleted")
        return super().delete(*args, **kwargs)



class JoinIssue(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse("home")

    def get(self, request, *args, **kwargs):
        issue = get_object_or_404(models.Issue,pk=self.kwargs.get("pk"))

        try:
            models.IssueMember.objects.create(user=self.request.user,issue=issue)

        except IntegrityError:
            messages.warning(self.request,("Warning, already a member of {}".format(issue.message)))

        else:
            messages.success(self.request,"You are now a member of the {} issue.".format(issue.message))

        return super().get(request, *args, **kwargs)


class LeaveIssue(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse("home")

    def get(self, request, *args, **kwargs):

        try:

            membership = models.IssueMember.objects.filter(
                user=self.request.user,
                issue__pk=self.kwargs.get("pk")
            ).get()

        except models.IssueMember.DoesNotExist:
            messages.warning(
                self.request,
                "You can't leave this issue because you aren't in it."
            )
        else:
            membership.delete()
            messages.success(
                self.request,
                "You have successfully left this issue."
            )
        return super().get(request, *args, **kwargs)

@login_required
def SolveIssue(request,pk):

    issue = models.Issue.objects.get(id=pk)
    issue.solve = True
    issue.save()
    return redirect('home')

@login_required
def UpdateIssue(request,pk):

    issue = models.Issue.objects.get(id=pk)
    form = forms.IssueForm(instance=issue)
    message=''   
        
    if request.method == 'POST':
        form = forms.IssueForm(request.POST,instance=issue)
        if form.is_valid():
            form.save()
            message = "issue edited successfully"
            return redirect('/')
        else:
            message = "Error, please check the details again"
 
    context = {'form':form,'message':message,'issue':issue}
    return render(request, 'issues/issue_update_form.html', context)

@login_required
def IssueDetail(request,pk):
    issue = models.Issue.objects.get(pk=pk)
    answer = models.Answer(user=request.user,issue=issue)
    form = forms.AnswerForm(instance=answer)
    accepted_answers = issue.answers.filter(accepted = True)
    potential_answers = issue.answers.filter(accepted = False)
    message = ''

    if request.method == 'POST':
        form = forms.AnswerForm(request.POST,instance=answer)
        if form.is_valid():
            form.save()
        else:
            message = "Error, please check the details again"

    context = {'issue':issue,'form':form,'message':message,'accepted_answers':accepted_answers,'potential_answers':potential_answers}
    return render(request,'issues/issue_detail.html',context)

@login_required
def like(request,pk):
    answer = models.Answer.objects.get(pk=pk)
    
    if answer.likes.filter(id=request.user.id).exists():
        answer.likes.remove(request.user)
    else:
        answer.likes.add(request.user)
    
    return HttpResponseRedirect(reverse('issues:single',args=[str(answer.issue.pk)]))

@login_required
def accept_answer(request,pk):

    answer = models.Answer.objects.get(pk=pk)
    issue = models.Issue.objects.get(pk=answer.issue.pk)
        
    if request.method == 'POST':
        answer.accepted = True
        answer.save()
        issue.solve = True
        issue.save()
        return HttpResponseRedirect(reverse('issues:single',args=[str(issue.pk)]))
    else:
        return render(request,'issues/answer_confirm.html',{'answer':answer,'issue':issue})