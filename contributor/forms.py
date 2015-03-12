from django import forms
from crispy_forms.bootstrap import FormActions, InlineRadios, PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Submit, Div, HTML
from mpinstaller.models import PackageVersion
from contributor.models import Contribution

ISSUE_TYPE_CHOICES = (
    ('existing', 'Existing Issue'),
    ('new', 'New Issue'),
)

CREATE_CONTRIBUTION_JS = """
<script type="text/javascript">
    function show_hide_issue_fields(radios) {
        var value = $(radios).val();
        if (value == 'existing') {
            $('.issue-existing').show();
            $('.issue-new').hide();
        } else if (value == 'new') {
            $('.issue-existing').hide();
            $('.issue-new').show();
        } else {
            $('.issue-existing').hide();
            $('.issue-new').hide();
        }
    }

    $(document).ready(function(){
        var issue_type = $("input[name='issue_type']");
        show_hide_issue_fields(issue_type.filter(':selected'));
        issue_type.click(function () {
            show_hide_issue_fields(this);
        });
    });
</script>
"""

class CreateContributionForm(forms.ModelForm):
    issue_type = forms.ChoiceField(choices=ISSUE_TYPE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(CreateContributionForm, self).__init__(*args, **kwargs)

        # Restrict package_version field to only PackageVersion objects which are the current github version on a Package
        self.fields['package_version'].queryset = PackageVersion.objects.filter(current_github__namespace__isnull = False)

        self.fields['title'].required = False
        self.fields['body'].required = False

        # django-crispy-forms FormHelper configuration
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            HTML(CREATE_CONTRIBUTION_JS),
            Field('contributor', type='hidden'),
            Fieldset(
                'Select a Package...',
                'package_version',
            ),
            Fieldset(
                'Select or Create an Issue...',
                InlineRadios('issue_type'),
                Div(
                    'github_issue',
                    css_class='issue-existing',
                ),
                Div(
                    'title',
                    'body',
                    css_class='issue-new',
                ),
            ),
            FormActions(
                Submit('submit', 'Submit')
            ),
        )

    class Meta:
        model = Contribution

    def save(self, commit=True):
        instance = super(CreateContributionForm, self).save(commit=False)
        issue = instance.get_issue()
        instance.title = issue['title']
        instance.body = issue['body']
        instance.github_issue = issue['number']
        if commit:
            instance.save()

        return instance

class ContributionEditBranchForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContributionEditBranchForm, self).__init__(*args, **kwargs)

        # django-crispy-forms FormHelper configuration
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            Fieldset(
                'Select a name for your branch...',
                PrependedText('fork_branch', 'feature/%s-' % self.instance.github_issue),
            ),
            FormActions(
                Submit('submit', 'Submit')
            ),
        )

    def save(self, commit=True):
        instance = super(ContributionEditBranchForm, self).save(commit=False)
        instance.fork_branch = 'feature/%s-%s' % (instance.github_issue, instance.fork_branch)
        if commit:
            instance.save()

        return instance

    class Meta:
        model = Contribution
        fields = ('fork_branch',)

class ContributionCommitForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ContributionCommitForm, self).__init__(*args, **kwargs)

        # django-crispy-forms FormHelper configuration
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            Fieldset(
                'Provide a description of your changes',
                'message',
            ),
            FormActions(
                Submit('submit', 'Submit')
            ),
        )

class ContributionSubmitForm(forms.Form):
    reviewer_notes = forms.CharField(widget=forms.Textarea, help_text="Add notes to the reviewer about your contribution")
    critical_changes = forms.CharField(required=False, widget=forms.Textarea, help_text="Briefly describe any changes end users must be aware of with your contribution or their system may not function as expected.")
    changes = forms.CharField(required=False, widget=forms.Textarea, help_text="Briefly describe any changes end users might need to make to enable new functionality from your contribution.")
    
    def __init__(self, *args, **kwargs):
        super(ContributionSubmitForm, self).__init__(*args, **kwargs)

        # django-crispy-forms FormHelper configuration
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            Fieldset(
                'Notes to reviewer',
                'reviewer_notes',
            ),
            Fieldset(
                'Release notes content',
                'critical_changes',
                'changes',
            ),
            FormActions(
                Submit('submit', 'Submit')
            ),
        )
    
