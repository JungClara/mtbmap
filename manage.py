#!/usr/bin/env python
import os, sys, np

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mtbmap.settings.local")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
