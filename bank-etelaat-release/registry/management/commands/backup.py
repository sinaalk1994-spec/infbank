import os, sqlite3, tempfile, zipfile, json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from registry.models import Document

class Command(BaseCommand):
    help='Create a consistent private backup of SQLite, archived documents and application key.'
    def add_arguments(self,parser): parser.add_argument('destination')
    def handle(self,*args,**options):
        destination=Path(options['destination']).resolve()
        if destination.exists(): raise CommandError('Destination exists; refusing to overwrite.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        source=sqlite3.connect(settings.DATABASES['default']['NAME'],timeout=20)
        lock=sqlite3.connect(settings.DATABASES['default']['NAME'],timeout=20)
        created=False
        try:
            # Block writers while database snapshot and immutable documents are copied.
            lock.execute('BEGIN IMMEDIATE')
            with tempfile.TemporaryDirectory() as temp:
                db=Path(temp)/'database.sqlite3'
                target=sqlite3.connect(db)
                try: source.backup(target)
                finally: target.close()
                fd=os.open(destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                created=True
                with os.fdopen(fd,'wb') as output, zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                    archive.write(db,'database.sqlite3')
                    archive.write(settings.RUNTIME/'secret.key','secret.key')
                    for name, in source.execute('SELECT file FROM registry_document'):
                        document=Path(settings.MEDIA_ROOT)/name
                        if not document.is_file(): raise CommandError(f'Missing archived file for record: {name}')
                        archive.write(document,'documents/'+name)
                    for logos in source.execute('SELECT logo, partner_logo, designer_logo FROM registry_settings'):
                        for name in logos:
                            if name: archive.write(Path(settings.MEDIA_ROOT)/name,'documents/'+name)
                    archive.writestr('manifest.json',json.dumps({'version':1,'database':'sqlite3','documents':'documents/'},indent=2))
            self.stdout.write(self.style.SUCCESS(f'Backup saved: {destination}'))
        except Exception:
            if created and destination.exists(): destination.unlink()
            raise
        finally:
            lock.rollback(); lock.close(); source.close()
