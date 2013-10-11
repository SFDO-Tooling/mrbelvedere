# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'JenkinsSite'
        db.create_table(u'mrbelvedere_jenkinssite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'mrbelvedere', ['JenkinsSite'])

        # Adding model 'Repository'
        db.create_table(u'mrbelvedere_repository', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'mrbelvedere', ['Repository'])

        # Adding model 'Branch'
        db.create_table(u'mrbelvedere_branch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Repository'])),
            ('github_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('jenkins_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'mrbelvedere', ['Branch'])

        # Adding model 'Job'
        db.create_table(u'mrbelvedere_job', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('auth_token', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.JenkinsSite'])),
        ))
        db.send_create_signal(u'mrbelvedere', ['Job'])

        # Adding model 'RepositoryNewBranchJob'
        db.create_table(u'mrbelvedere_repositorynewbranchjob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Repository'])),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Job'])),
        ))
        db.send_create_signal(u'mrbelvedere', ['RepositoryNewBranchJob'])

        # Adding model 'BranchJobTrigger'
        db.create_table(u'mrbelvedere_branchjobtrigger', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('branch', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Branch'])),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Job'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_trigger_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mrbelvedere', ['BranchJobTrigger'])

        # Adding model 'GithubUser'
        db.create_table(u'mrbelvedere_githubuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal(u'mrbelvedere', ['GithubUser'])

        # Adding model 'Push'
        db.create_table(u'mrbelvedere_push', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('branch', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.Branch'])),
            ('github_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrbelvedere.GithubUser'])),
            ('commit_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'mrbelvedere', ['Push'])


    def backwards(self, orm):
        # Deleting model 'JenkinsSite'
        db.delete_table(u'mrbelvedere_jenkinssite')

        # Deleting model 'Repository'
        db.delete_table(u'mrbelvedere_repository')

        # Deleting model 'Branch'
        db.delete_table(u'mrbelvedere_branch')

        # Deleting model 'Job'
        db.delete_table(u'mrbelvedere_job')

        # Deleting model 'RepositoryNewBranchJob'
        db.delete_table(u'mrbelvedere_repositorynewbranchjob')

        # Deleting model 'BranchJobTrigger'
        db.delete_table(u'mrbelvedere_branchjobtrigger')

        # Deleting model 'GithubUser'
        db.delete_table(u'mrbelvedere_githubuser')

        # Deleting model 'Push'
        db.delete_table(u'mrbelvedere_push')


    models = {
        u'mrbelvedere.branch': {
            'Meta': {'object_name': 'Branch'},
            'github_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jenkins_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.JenkinsSite']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'mrbelvedere.repositorynewbranchjob': {
            'Meta': {'object_name': 'RepositoryNewBranchJob'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Job']"}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"})
        }
    }

    complete_apps = ['mrbelvedere']