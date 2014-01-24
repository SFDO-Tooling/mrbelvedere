# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'PullRequest.github_user'
        db.add_column(u'mrbelvedere_pullrequest', 'github_user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['mrbelvedere.GithubUser']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'PullRequest.github_user'
        db.delete_column(u'mrbelvedere_pullrequest', 'github_user_id')


    models = {
        u'mrbelvedere.branch': {
            'Meta': {'object_name': 'Branch'},
            'github_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jenkins_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.Repository']"})
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
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.JenkinsSite']"})
        },
        u'mrbelvedere.pullrequest': {
            'Meta': {'object_name': 'PullRequest'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'github_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mrbelvedere.GithubUser']"}),
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