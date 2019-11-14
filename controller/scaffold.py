# -*- coding: utf-8 -*-

from jinja2 import FileSystemLoader, Environment
from pathlib import Path
from utilities.configuration import load_yaml_file
from utilities import helpers
from utilities import (
    PROJECT_DIR,
    BACKEND_DIR,
    MAIN_PACKAGE,
    SWAGGER_DIR,
    ENDPOINTS_CODE_DIR,
)
from controller import TEMPLATE_DIR, SUBMODULES_DIR
from utilities.logs import get_logger

log = get_logger(__name__)


class EndpointScaffold(object):
    """
    Scaffold necessary directories and file to create
    a new endpoint within the RAPyDo framework
    """

    def __init__(self, project, force=False, endpoint_name='foo', service_name=None):

        # custom init
        self.custom_project = project
        self.force_yes = force
        self.original_name = endpoint_name
        self.service_name = service_name

        names = []
        self.class_name = ''
        endpoint_name = endpoint_name.lstrip('/')
        for piece in endpoint_name.lower().replace(' ', '-').split('-'):
            if not piece.isalnum():
                log.exit("Only alpha-numeric chars are allowed: %s" % piece)
            else:
                names.append(piece)
                self.class_name += piece.capitalize()

        self.endpoint_dir = '_'.join(names)
        self.endpoint_name = self.endpoint_dir.replace('_', '')
        self.specs_file = 'specs.yaml'

        # setting the base dir for all scaffold things inside the project
        self.backend_dir = Path(PROJECT_DIR, self.custom_project, BACKEND_DIR)

        self.base_backend_dir = Path(SUBMODULES_DIR, BACKEND_DIR, MAIN_PACKAGE)

    def create(self):
        self.swagger()
        self.rest_class()
        self.test_class()
        log.info('Scaffold completed')

    def info(self):

        infos = '\n'
        base_endpoint = False
        endpoint = self.endpoint_name

        # look inside extended swagger definition
        backend = self.backend_dir
        needle = self.find_swagger(endpoint, backend)

        # or look inside base swagger definition of rapydo
        if needle is None:
            backend = self.base_backend_dir
            needle = self.find_swagger(endpoint, backend)
            base_endpoint = True
            python_file_dir = Path(backend, 'resources')
        else:
            python_file_dir = Path(backend, ENDPOINTS_CODE_DIR)

        if needle is None:
            log.exit('No endpoint "%s" found in current swagger definition' % endpoint)
        else:
            pass
            # log.pp(needle)

        current_dir = Path.cwd()

        uri = Path(needle.get('baseuri', '/api'), endpoint)
        infos += 'Endpoint path:\t%s\n' % uri

        swagger_dir = Path(
            current_dir, backend, SWAGGER_DIR, needle.get('swagger')
        )
        infos += 'Swagger path:\t%s/\n' % swagger_dir

        infos += 'Labels:\t\t%s\n' % ", ".join(needle.get('labels'))

        python_file_path = Path(
            current_dir, python_file_dir, needle.get('file') + '.py'
        )
        infos += 'Python file:\t%s\n' % python_file_path

        python_class = needle.get('class')
        infos += 'Python class:\t%s\n' % python_class

        log.info("Informations about '%s':\n%s", endpoint, infos)

        if base_endpoint:
            log.warning(
                "This is a BASE endpoint of the RAPyDo framework.\n"
                + "Do not modify it unless your are not a RAPyDo developer."
            )

        with open(str(python_file_path)) as fh:
            content = fh.read()
            if 'class %s(' % python_class not in content:
                log.critical(
                    "Class '%s' definition not found in python file" % python_class
                )

    def find_swagger(self, endpoint=None, backend_dir=None):

        swagdir = Path(backend_dir, SWAGGER_DIR)
        needle = None

        for current_specs_file in swagdir.glob('*/%s' % self.specs_file):
            content = load_yaml_file(str(current_specs_file))

            for _, value in content.get('mapping', {}).items():
                tmp = '/' + endpoint
                if value == tmp or value.startswith(tmp + '/'):
                    needle = content
                    mypath = str(current_specs_file).replace('/' + self.specs_file, '')
                    needle['swagger'] = helpers.last_dir(mypath)
                    break

            if needle is not None:
                break

        return needle

    def create_folder(self, pathobj):
        try:
            pathobj.mkdir(parents=False)
        except FileExistsError:
            pass

    def file_exists_and_nonzero(self, pathobj):

        if not pathobj.exists():
            return False

        iostats = pathobj.stat()
        return not iostats.st_size == 0

    def swagger_dir(self):

        self.swagger_path = Path(self.backend_dir, SWAGGER_DIR, self.endpoint_dir)

        if self.swagger_path.exists():
            log.warning('Path %s already exists' % self.swagger_path)
            if not self.force_yes:
                helpers.ask_yes_or_no(
                    'Would you like to proceed and overwrite definition?',
                    error='Cannot overwrite definition',
                )

        self.create_folder(self.swagger_path)

    @staticmethod
    def save_template(filename, content):
        with open(filename, "w") as fh:
            fh.write(content)

    def render(self, filename, data, outdir='custom', template_filename=None):

        mypath = Path(outdir, filename)
        if self.file_exists_and_nonzero(mypath):
            # # if you do not want to overwrite
            # log.warning("%s already exists" % filename)
            # return False
            log.info("%s already exists. Overwriting." % filename)

        filepath = str(mypath)
        template_dir = helpers.script_abspath(__file__, TEMPLATE_DIR)
        if template_filename is None:
            template_filename = filename

        # Simplify the usage of jinja2 templating.
        # https://www.pydanny.com/jinja2-quick-load-function.html
        loader = FileSystemLoader(template_dir)
        env = Environment(loader=loader)
        template = env.get_template(template_filename)
        templated_content = template.render(**data)

        self.save_template(filepath, templated_content)
        # NOTE: this below has to be INFO,
        # otherwise the user doesn't get info on what paths were created
        log.info("rendered %s" % filepath)
        return True

    def swagger_specs(self):
        self.render(
            self.specs_file,
            data={
                'endpoint_name': self.endpoint_name,
                'endpoint_label': self.endpoint_dir,
                'class_name': self.class_name,
            },
            outdir=self.swagger_path,
        )

    def swagger_first_operation(self):
        self.render(
            'get.yaml',
            data={'endpoint_name': self.endpoint_name},
            outdir=self.swagger_path,
        )

    def swagger(self):
        self.swagger_dir()
        self.swagger_specs()
        self.swagger_first_operation()

    def rest_class(self):

        filename = '%s.py' % self.endpoint_name
        self.class_path = Path(self.backend_dir, ENDPOINTS_CODE_DIR)
        filepath = Path(self.class_path, filename)

        if filepath.exists():
            log.warning('File %s already exists' % filepath)
            if not self.force_yes:
                helpers.ask_yes_or_no(
                    'Would you like to proceed and overwrite that code?',
                    error='Cannot overwrite the original file',
                )

        self.render(
            filename,
            template_filename='class.py',
            data={
                'endpoint_name': self.endpoint_name,
                'class_name': self.class_name,
                'service_name': self.service_name,
            },
            outdir=self.class_path,
        )

    def test_class(self):

        filename = 'test_%s.py' % self.endpoint_name
        self.tests_path = Path(self.backend_dir, 'tests')
        filepath = Path(self.tests_path, filename)

        if filepath.exists():
            log.warning('File %s already exists' % filepath)
            if not self.force_yes:
                helpers.ask_yes_or_no(
                    'Would you like to proceed and overwrite that code?',
                    error='Cannot overwrite the original file',
                )

        self.render(
            filename,
            template_filename='unittests.py',
            data={'endpoint_name': self.endpoint_name, 'class_name': self.class_name},
            outdir=self.tests_path,
        )
