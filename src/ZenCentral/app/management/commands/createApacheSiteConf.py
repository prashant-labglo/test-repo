from django.core.management.base import BaseCommand, CommandError
from LibLisa.config import lisaConfig

class Command(BaseCommand):
    help = "Generates site.conf which customizes the running of Apache according to host."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        with open(options["filename"][0], "w") as fp:
            print("ServerRoot {0}.format(lisaConfig.appRoot)")
            print("Define AppRootFolder '{0}src/'".format(lisaConfig.appRoot), file=fp)
            print("Define ModulesRootFolder {0}".format(lisaConfig.globalApacheModulesRoot), file=fp)
            print("Include '${AppRootFolder}ZenCentral/apache/httpd.conf'", file=fp)
            print("Include '${AppRootFolder}ZenCentral/apache/wsgi.conf'", file=fp)
            print("Include '${AppRootFolder}ZenCentral/apache/ssl.conf'", file=fp)
            print("Include '${AppRootFolder}ZenCentral/apache/zenApps.conf'", file=fp)