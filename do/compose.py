# -*- coding: utf-8 -*-

"""
Integration with Docker compose

# NOTE: A way to silence compose output:
https://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
"""

from compose.cli.command import \
    get_project_name, get_config_from_options, project_from_options
from compose.cli.main import TopLevelCommand
from do import PROJECT_DIR
from do.utils.logs import get_logger

log = get_logger(__name__)


class Compose(object):

    def __init__(self, files, options={}):
        super(Compose, self).__init__()

        self.files = files
        options.update({'--file': self.files})
        self.options = options

        self.project_dir = PROJECT_DIR
        self.project_name = get_project_name(self.project_dir)
        # log.very_verbose(f"Client compose '{self.project_name}': {files}")
        log.very_verbose("Client compose %s: %s" % (self.project_name, files))

    def config(self):
        _, services_list, _, _, _ = \
            get_config_from_options('.', self.options)
        # log.pp(services_list)
        return services_list

    def get_handle(self, command_dir):
        # TODO: check if this might be moved into __init__
        return TopLevelCommand(
            project_from_options(self.project_dir, self.options))

    def force_template_build(self, builds, options={}):

        compose_handler = self.get_handle(self.project_dir)
        force_options = {
            '--no-cache': True,
            '--pull': True,
        }

        for image_tag, build in builds.items():

            service = build.get('service')
            # compose_handler = self.get_handle(build.get('dir'))
            log.verbose("Building template for: %s" % service)

            # myoptions = {'SERVICE': [service], **force_options, **options}
            options.update(force_options)
            options.update({'SERVICE': [service]})
            log.pp(options)
            log.critical_exit("DEBUG ME HERE /2")

            compose_handler.build(options=options)
            log.info("Built template: %s" % service)

        return
