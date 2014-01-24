# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PullRequest'
        db.create_table(u'mrbelvedere_pullrequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Repository'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('message', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('source_branch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pull_requests_source', to=orm['mrbelvedere.Branch'])),
            ('target_branch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pull_requests_target', to=orm['mrbelvedere.Branch'])),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'mrbelvedere', ['PullRequest'])

        # Adding model 'RepositoryPullRequestJob'
        db.create_table(u'mrbelvedere_repositorypullrequestjob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Repository'])),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Job'])),
            ('forked', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('internal', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderated', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('repo_admins', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'mrbelvedere', ['RepositoryPullRequestJob'])

        # Adding M2M table for field admins on 'RepositoryPullRequestJob'
        m2m_table_name = db.shorten_name(u'mrbelvedere_repositorypullrequestjob_admins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('repositorypullrequestjob', models.ForeignKey(orm[u'mrbelvedere.repositorypullrequestjob'], null=False)),
            ('githubuser', models.ForeignKey(orm[u'mrbelvedere.githubuser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['repositorypullrequestjob_id', 'githubuser_id'])

        # Adding model 'PullRequestComment'
        db.create_table(u'mrbelvedere_pullrequestcomment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pull_request', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.PullRequest'])),
            ('github_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.GithubUser'])),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'mrbelvedere', ['PullRequestComment'])

        # Adding field 'Branch.name'
        db.add_column(u'mrbelvedere_branch', 'name',
                      self.gf('django.db.models.fields.CharField')(default='default_value', max_length=255),
                      keep_default=False)


        # Changing field 'GithubUser.email'
        db.alter_column(u'mrbelvedere_githubuser', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True))

        # Changing field 'GithubUser.name'
        db.alter_column(u'mrbelvedere_githubuser', 'name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))
        # Adding field 'Job.name'
        db.add_column(u'mrbelvedere_job', 'name',
                      self.gf('django.db.models.fields.CharField')(default='default_value', max_length=255),
                      keep_default=False)

        # Adding field 'Repository.name'
        db.add_column(u'mrbelvedere_repository', 'name',
                      self.gf('django.db.models.fields.CharField')(default='default_value', max_length=255),
                      keep_default=False)

        # Adding field 'Repository.forks'
        db.add_column(u'mrbelvedere_repository', 'forks',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Repository'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'PullRequest'
        db.delete_table(u'mrbelvedere_pullrequest')

        # Deleting model 'RepositoryPullRequestJob'
        db.delete_table(u'mrbelvedere_repositorypullrequestjob')

        # Removing M2M table for field admins on 'RepositoryPullRequestJob'
        db.delete_table(db.shorten_name(u'mrbelvedere_repositorypullrequestjob_admins'))

        # Deleting model 'PullRequestComment'
        db.delete_table(u'mrbelvedere_pullrequestcomment')

        # Deleting field 'Branch.name'
        db.delete_column(u'mrbelvedere_branch', 'name')


        # User chose to not deal with backwards NULL issues for 'GithubUser.email'
        raise RuntimeError("Cannot reverse this migration. 'GithubUser.email' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'GithubUser.email'
        db.alter_column(u'mrbelvedere_githubuser', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75))

        # User chose to not deal with backwards NULL issues for 'GithubUser.name'
        raise RuntimeError("Cannot reverse this migration. 'GithubUser.name' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'GithubUser.name'
        db.alter_column(u'mrbelvedere_githubuser', 'name', self.gf('django.db.models.fields.CharField')(max_length=255))
        # Deleting field 'Job.name'
        db.delete_column(u'mrbelvedere_job', 'name')

        # Deleting field 'Repository.name'
        db.delete_column(u'mrbelvedere_repository', 'name')

        # Deleting field 'Repository.forks'
        db.delete_column(u'mrbelvedere_repository', 'forks_id')


    models = {
        u'mrbelvedere.branch': {
            'Meta': {'object_name': 'Branch'},
            'github_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jenkins_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mrbelvedere.branchjobtrigger': {
            'Meta': {'object_name': 'BranchJobTrigger'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Branch']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Job']"}),
            'last_trigger_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mrbelvedere.githubuser': {
            'Meta': {'object_name': 'GithubUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mrbelvedere.jenkinssite': {
            'Meta': {'object_name': 'JenkinsSite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'mrbelvedere.job': {
            'Meta': {'object_name': 'Job'},
            'auth_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.JenkinsSite']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mrbelvedere.pullrequest': {
            'Meta': {'object_name': 'PullRequest'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"}),
            'source_branch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pull_requests_source'", 'to': u"orm['mrbelvedere.Branch']"}),
            'target_branch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pull_requests_target'", 'to': u"orm['mrbelvedere.Branch']"})
        },
        u'mrbelvedere.pullrequestcomment': {
            'Meta': {'object_name': 'PullRequestComment'},
            'github_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.GithubUser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'pull_request': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.PullRequest']"})
        },
        u'mrbelvedere.push': {
            'Meta': {'object_name': 'Push'},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Branch']"}),
            'commit_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'github_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.GithubUser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mrbelvedere.repository': {
            'Meta': {'object_name': 'Repository'},
            'forks': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'mrbelvedere.repositorynewbranchjob': {
            'Meta': {'object_name': 'RepositoryNewBranchJob'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Job']"}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"})
        },
        u'mrbelvedere.repositorypullrequestjob': {
            'Meta': {'object_name': 'RepositoryPullRequestJob'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mrbelvedere.GithubUser']", 'symmetrical': 'False'}),
            'forked': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Job']"}),
            'moderated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'repo_admins': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"})
        }
    }

    complete_apps = ['mrbelvedere']