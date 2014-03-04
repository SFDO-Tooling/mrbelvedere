# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'PackageVersionCondition'
        db.delete_table(u'mpinstaller_packageversioncondition')

        # Adding model 'MetadataCondition'
        db.create_table(u'mpinstaller_metadatacondition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('metadata_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('search', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('exclude_namespaces', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'mpinstaller', ['MetadataCondition'])

        # Adding M2M table for field conditions on 'PackageVersion'
        m2m_table_name = db.shorten_name(u'mpinstaller_packageversion_conditions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('packageversion', models.ForeignKey(orm[u'mpinstaller.packageversion'], null=False)),
            ('metadatacondition', models.ForeignKey(orm[u'mpinstaller.metadatacondition'], null=False))
        ))
        db.create_unique(m2m_table_name, ['packageversion_id', 'metadatacondition_id'])


    def backwards(self, orm):
        # Adding model 'PackageVersionCondition'
        db.create_table(u'mpinstaller_packageversioncondition', (
            ('exclude_namespaces', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='conditions', to=orm['mpinstaller.PackageVersion'])),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('metadata_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('compare_on', self.gf('django.db.models.fields.CharField')(max_length=255)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'mpinstaller', ['PackageVersionCondition'])

        # Deleting model 'MetadataCondition'
        db.delete_table(u'mpinstaller_metadatacondition')

        # Removing M2M table for field conditions on 'PackageVersion'
        db.delete_table(db.shorten_name(u'mpinstaller_packageversion_conditions'))


    models = {
        u'mpinstaller.metadatacondition': {
            'Meta': {'object_name': 'MetadataCondition'},
            'exclude_namespaces': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'search': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'mpinstaller.package': {
            'Meta': {'ordering': "['namespace']", 'object_name': 'Package'},
            'current_beta': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_beta'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'current_prod': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'current_prod'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'mpinstaller.packageinstallation': {
            'Meta': {'object_name': 'PackageInstallation'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'org_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'org_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mpinstaller.Package']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mpinstaller.PackageVersion']", 'null': 'True', 'blank': 'True'})
        },
        u'mpinstaller.packageversion': {
            'Meta': {'ordering': "['package__namespace', 'number']", 'object_name': 'PackageVersion'},
            'conditions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mpinstaller.MetadataCondition']", 'symmetrical': 'False'}),
            'git_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['mpinstaller.Package']"}),
            'subdir': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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