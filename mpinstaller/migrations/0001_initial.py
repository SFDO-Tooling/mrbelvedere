# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Package'
        db.create_table(u'mpinstaller_package', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namespace', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('current_version', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='current_version', null=True, to=orm['mpinstaller.PackageVersion'])),
        ))
        db.send_create_signal(u'mpinstaller', ['Package'])

        # Adding model 'PackageVersion'
        db.create_table(u'mpinstaller_packageversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['mpinstaller.Package'])),
            ('beta', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'mpinstaller', ['PackageVersion'])

        # Adding model 'PackageVersionDependency'
        db.create_table(u'mpinstaller_packageversiondependency', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dependencies', to=orm['mpinstaller.PackageVersion'])),
            ('requires', self.gf('django.db.models.fields.related.ForeignKey')(related_name='required_by', to=orm['mpinstaller.PackageVersion'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mpinstaller', ['PackageVersionDependency'])


    def backwards(self, orm):
        # Deleting model 'Package'
        db.delete_table(u'mpinstaller_package')

        # Deleting model 'PackageVersion'
        db.delete_table(u'mpinstaller_packageversion')

        # Deleting model 'PackageVersionDependency'
        db.delete_table(u'mpinstaller_packageversiondependency')


    models = {
        u'mpinstaller.package': {
            'Meta': {'ordering': "['namespace']", 'object_name': 'Package'},
            'current_version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_version'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
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