import zipfile
from io import BytesIO
from urllib.parse import quote

from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from django.template import Context, Template, TemplateSyntaxError

from rdmo.projects.exports import Export
from rdmo.services.providers import OauthProviderMixin
from rdmo.views.models import View
from rdmo.core.utils import render_to_format
from rdmo import __version__
from rdmo.core.pandoc import get_pandoc_version
from rdmo.projects.utils import get_value_path
from rdmo.views.utils import ProjectWrapper

class ReadmeExport(OauthProviderMixin, Export):
    class Form(forms.Form):
        view_uri = forms.CharField(
            label=_("Template view's URI"),
            help_text=_('Change this field only if you want to provide your own template view.'),
            initial='https://rdmo-hackathon-25.de/terms/views/rdmo-readme'
        )

        datasets = forms.MultipleChoiceField(
            label=_('Project dataset(s)'),
            help_text=_('One README file will be created for each selected choice. If you want a single README file with all datasets, please select the last choice.'),
            widget=forms.CheckboxSelectMultiple,
            choices=[]
        )

        def __init__(self, *args, **kwargs):
            dataset_choices = kwargs.pop('dataset_choices')
            super().__init__(*args, **kwargs)

            self.fields['datasets'].choices = [*dataset_choices, ('all', _('All datasets in one file'))]

    def render(self):
        datasets = self.get_set('project/dataset/id')
        if len(datasets) == 0:
            return render(self.request, 'core/error.html', {
                    'title': _('There are no datasets defined yet'),
                    'errors': [_('Please put some information in your data management plan.')]
                }, status=200)

        dataset_choices = [(dataset.set_index, dataset.value)for dataset in datasets]

        self.store_in_session(self.request, 'dataset_choices', dataset_choices)

        form = self.Form(dataset_choices=dataset_choices)
        return render(self.request, 'plugins/exports_readme.html', {'form': form}, status=200)

    def submit(self):
        dataset_choices = self.get_from_session(self.request, 'dataset_choices')
        form = self.Form(self.request.POST, dataset_choices=dataset_choices)

        if 'cancel' in self.request.POST:
            return redirect('project', self.project.id)

        if form.is_valid():
            response = self.render_readme(form.cleaned_data, self.project, self.snapshot)

            if response is None:
                return render(self.request, 'core/error.html', {
                    'title': _('Something went wrong'),
                    'errors': [_('The README could not be created.')]
                }, status=200)
            
            return response

        else:
            return render(self.request, 'plugins/exports_readme.html', {'form': form}, status=200)
        
    def zip(self, content_files):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(
            file=zip_buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as zip_archive:
            for name, file_content in content_files.items():
                zip_archive.writestr(
                    zinfo_or_arcname=quote(name, encoding='utf-8'), 
                    data=file_content
                )

        zip_buffer.seek(0)

        return zip_buffer
    
    def render_readme(self, form_data, project, snapshot=None):
        view_uri = form_data['view_uri'] 
        dataset_choices = form_data['datasets']        

        project_datasets = self.get_set('project/dataset/id')
        contents = {}

        try:
            view = View.objects.get(uri=view_uri)
        except:
            view = View.objects.get(uri='https://rdmo-hackathon-25.de/terms/views/rdmo-readme')

        for choice in dataset_choices:
            dataset = None if choice == 'all' else project_datasets[int(choice)].as_dict
            try:
                site = Site.objects.get_current()
                project_wrapper = ProjectWrapper(project, snapshot)
                rendered_view = Template(view.template).render(Context({
                    'project': project_wrapper,
                    'conditions': project_wrapper.conditions,
                    'dataset': dataset,
                    'format': 'plain',
                    'rdmo_version': __version__,
                    'site': {
                        'name': site.name,
                        'domain': site.domain
                    },
                    'pandoc_version': get_pandoc_version().major
                }))
            except TemplateSyntaxError:
                continue

            title = (
                project.title.lower().replace(" ", "_") if choice == 'all' else 
                project_datasets[int(choice)].value.lower().replace(' ', '_')
            )
            response = render_to_format(
                None, 'plain', title, 'projects/project_view_export.html', {
                'format': 'plain',
                'title': title,
                'view': view,
                'rendered_view': rendered_view,
                'resource_path': get_value_path(project, snapshot)
                }
            )
            contents[title] = response.content

        if len(contents) == 1:
            content = list(contents.values())[0]
            content_type = 'text/plain'
            file_name = 'README.txt'
            content_disposition = f'attachment; filename="{file_name}"'

        elif len(contents) > 1:
            content = self.zip(contents)
            content_type = 'application/zip'
            file_name = 'project_readmes.zip'
            content_disposition = f'attachment; filename="{file_name}"'

        else:
            return None
        
        response = HttpResponse(
            content,
            headers={
                "Content-Type": content_type,
                "Content-Disposition": content_disposition,
            },
        )
        return response