# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PackageInstallationStep'
        db.create_table(u'mpinstaller_packageinstallationstep', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('installation', self.gf('django.db.models.fields.related.ForeignKey')(related_name='packages', to=orm['mpinstaller.PackageInstallation'])),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='installation_steps', null=True, to=orm['mpinstaller.Package'])),
            ('package_version', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='installation_steps', null=True, to=orm['mpinstaller.PackageVersion'])),
            ('previous_version', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('log', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'mpinstaller', ['PackageInstallationStep'])

        # Adding model 'PackageInstallationSession'
        db.create_table(u'mpinstaller_packageinstallationsession', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('installation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mpinstaller.PackageInstallation'])),
            ('oauth', self.gf('django.db.models.fields.TextField')()),
            ('org_packages', self.gf('django.db.models.fields.TextField')()),
            ('metadata', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'mpinstaller', ['PackageInstallationSession'])

        # Deleting field 'PackageVersion.subdir'
        db.delete_column(u'mpinstaller_packageversion', 'subdir')

        # Deleting field 'PackageInstallation.action'
        db.delete_column(u'mpinstaller_packageinstallation', 'action')

        # Adding field 'PackageInstallation.install_map'
        db.add_column(u'mpinstaller_packageinstallation', 'install_map',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'PackageInstallationStep'
        db.delete_table(u'mpinstaller_packageinstallationstep')

        # Deleting model 'PackageInstallationSession'
        db.delete_table(u'mpinstaller_packageinstallationsession')

        # Adding field 'PackageVersion.subdir'
        db.add_column(u'mpinstaller_packageversion', 'subdir',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'PackageInstallation.action'
        raise RuntimeError("Cannot reverse this migration. 'PackageInstallation.action' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'PackageInstallation.action'
        db.add_column(u'mpinstaller_packageinstallation', 'action',
                      self.gf('django.db.models.fields.CharField')(max_length=32),
                      keep_default=False)

        # Deleting field 'PackageInstallation.install_map'
        db.delete_column(u'mpinstaller_packageinstallation', 'install_map')


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
            'installation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mpinstaller.PackageInstallation']"}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'oauth': ('django.db.models.fields.TextField', [], {}),
            'org_packages': ('django.db.models.fields.TextField', [], {})
        },
        u'mpinstaller.packageinstallationstep': {
            'Meta': {'object_name': 'PackageInstallationStep'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': u"orm['mpinstaller.PackageInstallation']"}),
            'log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installation_steps'", 'null': 'True', 'to': u"orm['mpinstaller.Package']"}),
            'package_version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'installation_steps'", 'null': 'True', 'to': u"orm['mpinstaller.PackageVersion']"}),
            'previous_version': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'mpinstaller.packageversion': {
            'Meta': {'ordering': "['package__namespace', 'number']", 'object_name': 'PackageVersion'},
            'conditions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mpinstaller.MetadataCondition']", 'null': 'True', 'blank': 'True'}),
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