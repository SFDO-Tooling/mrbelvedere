# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'PackageVersion.content_success'
        db.add_column(u'mpinstaller_packageversion', 'content_success',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'PackageVersion.content_failure'
        db.add_column(u'mpinstaller_packageversion', 'content_failure',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'PackageVersion.content_success_beta'
        db.add_column(u'mpinstaller_packageversion', 'content_success_beta',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'PackageVersion.content_failure_beta'
        db.add_column(u'mpinstaller_packageversion', 'content_failure_beta',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Package.content_intro'
        db.add_column(u'mpinstaller_package', 'content_intro',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Package.content_success'
        db.add_column(u'mpinstaller_package', 'content_success',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Package.content_failure'
        db.add_column(u'mpinstaller_package', 'content_failure',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Package.content_success_beta'
        db.add_column(u'mpinstaller_package', 'content_success_beta',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Package.content_failure_beta'
        db.add_column(u'mpinstaller_package', 'content_failure_beta',
                      self.gf('tinymce.models.HTMLField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'PackageVersion.content_success'
        db.delete_column(u'mpinstaller_packageversion', 'content_success')

        # Deleting field 'PackageVersion.content_failure'
        db.delete_column(u'mpinstaller_packageversion', 'content_failure')

        # Deleting field 'PackageVersion.content_success_beta'
        db.delete_column(u'mpinstaller_packageversion', 'content_success_beta')

        # Deleting field 'PackageVersion.content_failure_beta'
        db.delete_column(u'mpinstaller_packageversion', 'content_failure_beta')

        # Deleting field 'Package.content_intro'
        db.delete_column(u'mpinstaller_package', 'content_intro')

        # Deleting field 'Package.content_success'
        db.delete_column(u'mpinstaller_package', 'content_success')

        # Deleting field 'Package.content_failure'
        db.delete_column(u'mpinstaller_package', 'content_failure')

        # Deleting field 'Package.content_success_beta'
        db.delete_column(u'mpinstaller_package', 'content_success_beta')

        # Deleting field 'Package.content_failure_beta'
        db.delete_column(u'mpinstaller_package', 'content_failure_beta')


    models = {
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
            'content_success': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'current_beta': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_beta'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'current_prod': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_prod'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mpinstaller.packageinstallation': {
            'Meta': {'object_name': 'PackageInstallation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'install_map': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'org_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'org_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'installations'", 'to': u"orm['mpinstaller.Package']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installations'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"})
        },
        u'mpinstaller.packageinstallationsession': {
            'Meta': {'object_name': 'PackageInstallationSession'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sessions'", 'to': u"orm['mpinstaller.PackageInstallation']"}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'oauth': ('django.db.models.fields.TextField', [], {}),
            'org_packages': ('django.db.models.fields.TextField', [], {})
        },
        u'mpinstaller.packageinstallationstep': {
            'Meta': {'ordering': "['order']", 'object_name': 'PackageInstallationStep'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'steps'", 'to': u"orm['mpinstaller.PackageInstallation']"}),
            'log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installation_steps'", 'null': 'True', 'to': u"orm['mpinstaller.Package']"}),
            'previous_version': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installation_steps'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"})
        },
        u'mpinstaller.packageversion': {
            'Meta': {'ordering': "['package__namespace', 'number']", 'object_name': 'PackageVersion'},
            'conditions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mpinstaller.MetadataCondition']", 'null': 'True', 'blank': 'True'}),
            'content_failure': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_failure_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'content_success_beta': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['mpinstaller.Package']"}),
            'zip_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mpinstaller.packageversiondependency': {
            'Meta': {'ordering': "['order']", 'object_name': 'PackageVersionDependency'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'requires': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'required_by'", 'to': u"orm['mpinstaller.PackageVersion']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dependencies'", 'to': u"orm['mpinstaller.PackageVersion']"})
        }
    }

    complete_apps = ['mpinstaller']