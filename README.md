# fix_include_statements

This script checks a codebase for inconsistencies between the include statements in the files and the actual filenames in the filesystem. These inconsistensies can be a problem on case-sensitive filesystems, such as Linux, and can cause build errors. The script lists all the inconsistencies and allows the user to fix them by choosing the correct filename from the filesystem. The script is intended to be run from the top-level directory of the codebase.

Run the script with the `-h` or `--help` flag for more information.
