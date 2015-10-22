# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Contribution.date_started'
        db.add_column(u'contributor_contribution', 'date_started',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2015, 10, 22, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Contribution.date_modified'
        db.add_column(u'contributor_contribution', 'date_modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2015, 10, 22, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Contribution.release_url'
        db.add_column(u'contributor_contribution', 'release_url',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Contribution.date_started'
        db.delete_column(u'contributor_contribution', 'date_started')

        # Deleting field 'Contribution.date_modified'
        db.delete_column(u'contributor_contribution', 'date_modified')

        # Deleting field 'Contribution.release_url'
        db.delete_column(u'contributor_contribution', 'release_url')


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
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_branch_synced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fork_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fork_merge_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fork_pull': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'github_issue': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_deployed_commit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_deployed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_deployment_installation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contributions'", 'null': 'True', 'to': u"orm['mpinstaller.PackageInstallation']"}),
            'last_retrieve_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'main_branch': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'main_pull': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'package_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contributions'", 'to': u"orm['mpinstaller.PackageVersion']"}),
            'release_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sf_oauth': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'state_behind_main': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_uncommitted_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_undeployed_commit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contributor.contributionsync': {
            'Meta': {'object_name': 'ContributionSync'},
            'contribution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'syncs'", 'to': u"orm['contributor.Contribution']"}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'new_commit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'new_installation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contribution_syncs'", 'null': 'True', 'to': u"orm['mpinstaller.PackageInstallation']"}),
            'post_state_behind_main': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_state_uncommitted_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_state_undeployed_commit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_state_behind_main': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_state_uncommitted_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_state_undeployed_commit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '32'})
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
        u'mpinstaller.packageinstallation': {
            'Meta': {'ordering': "['-created']", 'object_name': 'PackageInstallation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fork': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'git_ref': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'install_map': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'instance_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'org_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'org_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'installations'", 'to': u"orm['mpinstaller.Package']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installations'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"})
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
            'package_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'repo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'subfolder': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['contributor']