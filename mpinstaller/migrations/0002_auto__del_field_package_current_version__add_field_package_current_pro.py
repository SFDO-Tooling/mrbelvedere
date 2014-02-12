# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Package.current_version'
        db.delete_column(u'mpinstaller_package', 'current_version_id')

        # Adding field 'Package.current_prod'
        db.add_column(u'mpinstaller_package', 'current_prod',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='current_prod', null=True, to=orm['mpinstaller.PackageVersion']),
                      keep_default=False)

        # Adding field 'Package.current_beta'
        db.add_column(u'mpinstaller_package', 'current_beta',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='current_beta', null=True, to=orm['mpinstaller.PackageVersion']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Package.current_version'
        db.add_column(u'mpinstaller_package', 'current_version',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='current_version', null=True, to=orm['mpinstaller.PackageVersion'], blank=True),
                      keep_default=False)

        # Deleting field 'Package.current_prod'
        db.delete_column(u'mpinstaller_package', 'current_prod_id')

        # Deleting field 'Package.current_beta'
        db.delete_column(u'mpinstaller_package', 'current_beta_id')


    models = {
        u'mpinstaller.package': {
            'Meta': {'ordering': "['namespace']", 'object_name': 'Package'},
            'current_beta': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_beta'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'current_prod': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_prod'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mpinstaller.packageversion': {
            'Meta': {'ordering': "['package__namespace', 'number']", 'object_name': 'PackageVersion'},
            'beta': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['mpinstaller.Package']"})
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