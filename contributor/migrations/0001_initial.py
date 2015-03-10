# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Contributor'
        db.create_table(u'contributor_contributor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contributors', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'contributor', ['Contributor'])

        # Adding model 'Contribution'
        db.create_table(u'contributor_contribution', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('package_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contributions', to=orm['mpinstaller.PackageVersion'])),
            ('contributor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contributions', to=orm['contributor.Contributor'])),
            ('sf_oauth', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('github_issue', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fork_branch', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('fork_merge_branch', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('main_branch', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('fork_pull', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('main_pull', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_behind_main', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state_undeployed_commit', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state_uncommitted_changes', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_deployed_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_deployed_commit', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('last_retrieve_checksum', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'contributor', ['Contribution'])


    def backwards(self, orm):
        # Deleting model 'Contributor'
        db.delete_table(u'contributor_contributor')

        # Deleting model 'Contribution'
        db.delete_table(u'contributor_contribution')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'contributor.contribution': {
            'Meta': {'object_name': 'Contribution'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'contributor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contributions'", 'to': u"orm['contributor.Contributor']"}),
            'fork_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fork_merge_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fork_pull': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'github_issue': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_deployed_commit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_deployed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_retrieve_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'main_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'main_pull': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'package_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contributions'", 'to': u"orm['mpinstaller.PackageVersion']"}),
            'sf_oauth': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'state_behind_main': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_uncommitted_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_undeployed_commit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contributor.contributor': {
            'Meta': {'object_name': 'Contributor'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contributors'", 'to': u"orm['auth.User']"})
        },
        u'mpinstaller.metadatacondition': {
            'Meta': {'object_name': 'MetadataCondition'},
            'exclude_namespaces': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'no_match': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'search': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'mpinstaller.package': {
            'Meta': {'ordering': "['namespace']", 'object_name': 'Package'},
            'content_failure': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_failure_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_intro': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_intro_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'current_beta': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_beta'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'current_github': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_github'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'current_prod': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_prod'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'force_sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.SlugField', [], {'max_length': '128'})
        },
        u'mpinstaller.packageversion': {
            'Meta': {'ordering': "['package__namespace', 'number']", 'object_name': 'PackageVersion'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'conditions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mpinstaller.MetadataCondition']", 'null': 'True', 'blank': 'True'}),
            'content_failure': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_intro': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'github_password': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'github_username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'namespace_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['mpinstaller.Package']"}),
            'repo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subfolder': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['contributor']