from django.core.management.base import BaseCommand, CommandError
from LibLisa.config import lisaConfig

class Command(BaseCommand):
    help = "Generates site.conf which customizes the running of Apache according to host."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        with open(options["filename"][0], "w") as fp:
            print("ServerRoot {0}".format(lisaConfig.appRoot), file=fp)
            print("Define ZenAppsRootFolder '{0}src/'".format(lisaConfig.appRoot), file=fp)
            print("Define ModulesRootFolder {0}".format(lisaConfig.globalApacheModulesRoot), file=fp)
            print("Define ServicePort {0}".format(lisaConfig.apacheConfig.http_port), file=fp)
            print("Define ServerName {0}".format(lisaConfig.apacheConfig.http_host), file=fp)
            print("Define SslCertFile {0}".format(lisaConfig.apacheConfig.ssl_crt), file=fp)
            print("Define SslKeyFile {0}".format(lisaConfig.apacheConfig.ssl_key), file=fp)
            print("Define ServiceUrl {0}".format(lisaConfig.apacheConfig.service_url), file=fp)
            print("Define AngularAppRootFolder {0}".format(lisaConfig.angularAppRootFolder), file=fp)
            print("Include '${ZenAppsRootFolder}ZenCentral/apache/httpd.conf'", file=fp)
            print("Include '${ZenAppsRootFolder}ZenCentral/apache/wsgi.conf'", file=fp)
            print("Include '${ZenAppsRootFolder}ZenCentral/apache/ssl.conf'", file=fp)
            print("Include '${ZenAppsRootFolder}ZenCentral/apache/zenApps.conf'", file=fp)
            print("Include '${ZenAppsRootFolder}ZenCentral/apache/openidc.conf'", file=fp)
