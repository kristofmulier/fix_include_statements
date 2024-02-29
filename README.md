# fix_include_statements

This script checks a codebase for inconsistencies between the include statements in the files and the actual filenames in the filesystem. These inconsistensies can be a problem on case-sensitive filesystems, such as Linux, and can cause build errors. The script lists all the inconsistencies and allows the user to fix them by choosing the correct filename from the filesystem. The script is intended to be run from the top-level directory of the codebase.

```
Usage: python fix_include_statements.py [options]

Options:
--------
  -h, --help                                   Show this help message and exit.

  -n, --dry-run                                Print the results without fixing the
                                               include statements.

  -d DIRECTORY,                                Toplevel directory of the codebase
  --directory=DIRECTORY                        to process. If not provided,
                                               the current directory is used.

Examples:
---------
  Show the inconsistencies in the codebase, assuming that this script is in the
  top-level directory:
      > python fix_include_statements.py --dry-run

  Fix the inconsistencies:
      > python fix_include_statements.py
```
