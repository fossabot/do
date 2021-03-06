# -*- coding: utf-8 -*-

"""
    Command line script: main function
"""

from controller import log


def main():
    try:
        # imported here to avoid uncatched Keyboard Interruptions
        from controller.arguments import ArgParser

        arguments = ArgParser()

        from controller.app import Application

        Application(arguments)
    except KeyboardInterrupt:
        log.info("Interrupted by the user")
    except NotImplementedError as e:
        print('NOT IMPLEMENTED (yet): {}'.format(e))
    else:
        log.verbose("Application completed")


if __name__ == '__main__':
    main()
