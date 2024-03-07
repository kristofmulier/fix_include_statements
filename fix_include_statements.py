# -*- coding: utf-8 -*-
"""
Copyright 2024 Kristof Mulier.
"""
# SUMMARY:
# This script is used to check the codebase for inconsistencies between the include statements in
# the files and the actual filenames in the filesystem. These inconsistencies can be a problem on
# case-sensitive filesystems, such as Linux, and can cause build errors. The script lists all the
# inconsistencies and allows the user to fix them by choosing the correct filename from the
# filesystem. Additionally, it corrects backslashes in include statements to use forward slashes
# for better cross-platform compatibility. The script is intended to be run from the top-level
# directory of the codebase.
import os
import re
import argparse
import sys
from typing import Dict, List, Tuple

def print_help() -> None:
    '''
    Print the help message.
    '''
    print(
        "\n"
        "fix_include_statements.py\n"
        "=========================\n"
        "This script is used to check the codebase for inconsistencies between the include\n"
        "statements in the files and the actual filenames in the filesystem, and to correct\n"
        "backslashes in include statements to use forward slashes. These inconsistencies can\n"
        "be a problem on case-sensitive filesystems, such as Linux, and can cause build errors.\n"
        "The script lists all the inconsistencies and allows the user to fix them by choosing\n"
        "the correct filename from the filesystem. The script is intended to be run from the\n"
        "top-level directory of the codebase.\n"
        "\n"
        "Usage: python fix_include_statements.py [options]\n"
        "\n"
        "Options:\n"
        "--------\n"
        "  -h, --help                                   Show this help message and exit.\n"
        "\n"
        "  -n, --dry-run                                Print the results without fixing the\n"
        "                                               include statements.\n"
        "\n"
        "  -d DIRECTORY,                                Toplevel directory of the codebase\n"
        "  --directory=DIRECTORY                        to process. If not provided,\n"
        "                                               the current directory is used.\n"
        "\n"
        "Examples:\n"
        "---------\n"
        "  Show the inconsistencies in the codebase, assuming that this script is in the \n"
        "  top-level directory:\n"
        "      > python fix_include_statements.py --dry-run\n"
        "\n"
        "  Fix the inconsistencies and backslashes in include statements:\n"
        "      > python fix_include_statements.py\n"
        "\n"
    )
    return

def crawl_codebase(root_dir: str) -> Dict[str, List[str]]:
    '''
    Crawls the codebase and returns a dictionary with the relative path of each file as key and a
    list of its includes as value.
    '''
    include_pattern = re.compile(r'#include\s*["<](.*?)[">]')
    include_dict: Dict[str, List[str]] = {}

    print("Crawling the codebase")
    i = 0
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if not filename.endswith(('.h', '.hpp', '.c', '.cpp')):
                continue
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, start=root_dir).replace('\\', '/')
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                include_list: List[str] = include_pattern.findall(content)
                # include_list = [include.replace('\\', '/') for include in include_list]
                if include_list:
                    include_dict[relative_path] = include_list
            i += 1
            if i % 100 == 0:
                print(".", end="")
                sys.stdout.flush()
            continue
        continue
    print("")
    return include_dict

def list_all_files(root_dir: str) -> Dict[str, List[Tuple[str, str]]]:
    '''
    Lists all filenames in the codebase with extensions .h, .hpp, .c, and .cpp, mapping lower case
    filenames to their actual cases and relative paths in the filesystem.
    '''
    filename_dict: Dict[str, List[Tuple[str, str]]] = {}

    print("Listing all filenames")
    i = 0
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if not filename.endswith(('.h', '.hpp', '.c', '.cpp')):
                continue
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, start=root_dir).replace('\\', '/')
            lower_filename = filename.lower()
            if lower_filename not in filename_dict:
                filename_dict[lower_filename] = [(filename, relative_path)]
            else:
                filename_dict[lower_filename].append((filename, relative_path))
            i += 1
            if i % 100 == 0:
                print(".", end="")
                sys.stdout.flush()
            continue
        continue
    print("")
    return filename_dict

def check_codebase(root_dir: str, dry_run:bool) -> None:
    '''
    Checks the codebase for inconsistencies between the include statements in the files and the
    actual filenames in the filesystem, and corrects backslashes in include statements to use
    forward slashes.
    '''
    include_dict: Dict[str, List[str]] = crawl_codebase(root_dir)
    all_filenames: Dict[str, List[Tuple[str, str]]] = list_all_files(root_dir)

    results = {}
    print("Analyzing the codebase")
    i = 0
    # Loop over all the files and their include statements
    for path, include_list in include_dict.items():
        # Loop over all the include statements in the file (more precisely - the values of these
        # include statements, which are the filenames of the included files, or sometimes relative
        # paths to the included files).
        for include_statement_value in include_list:
            i += 1
            if i % 100 == 0:
                print(".", end="")
                sys.stdout.flush()
            include_filename_lower = include_statement_value.replace('\\', '/').split('/')[-1].lower()
            if include_filename_lower not in all_filenames:
                # The include statement refers to a file that does not exist in the filesystem. This
                # could be an include from a file in the compiler toolchain (eg. string.h). We skip,
                # but not before checking for backslashes.
                if '\\' in include_statement_value:
                    if path in results:
                        results[path][include_statement_value] = {
                            'actual_filenames': [None, ],
                            'actual_paths'    : [None, ],
                        }
                    else:
                        results[path] = {
                            include_statement_value: {
                                'actual_filenames': [None, ],
                                'actual_paths'    : [None, ],
                            },
                        }
                continue

            # Extract the matches - a list of tuples with the actual filename and its relative path.
            # Each tuple is a possible candidate for the file that the include statement refers to.
            matches: List[Tuple[str, str]] = all_filenames[include_filename_lower]

            # Only one match
            if len(matches) == 1:
                actual_filename, actual_path = matches[0]
                if actual_filename != include_statement_value.replace('\\', '/').split('/')[-1]:
                    if path in results:
                        results[path][include_statement_value] = {
                            'actual_filenames': [actual_filename, ],
                            'actual_paths'    : [actual_path, ],
                        }
                    else:
                        results[path] = {
                            include_statement_value: {
                                'actual_filenames': [actual_filename, ],
                                'actual_paths'    : [actual_path, ],
                            },
                        }
                else:
                    # Still check for backslashes
                    if '\\' in include_statement_value:
                        if path in results:
                            results[path][include_statement_value] = {
                                'actual_filenames': [None, ],
                                'actual_paths'    : [None, ],
                            }
                        else:
                            results[path] = {
                                include_statement_value: {
                                    'actual_filenames': [None, ],
                                    'actual_paths'    : [None, ],
                                },
                            }
            # Multiple matches
            else:
                actual_filenames = []
                actual_paths = []
                filename_matches: bool = False
                for match in matches:
                    actual_filename, actual_path = match
                    actual_filenames.append(actual_filename)
                    actual_paths.append(actual_path)
                    if actual_filename == include_statement_value.replace('\\', '/').split('/')[-1]:
                        filename_matches = True
                if not filename_matches:
                    if path in results:
                        results[path][include_statement_value] = {
                            'actual_filenames': actual_filenames,
                            'actual_paths'    : actual_paths,
                        }
                    else:
                        results[path] = {
                            include_statement_value: {
                                'actual_filenames': actual_filenames,
                                'actual_paths'    : actual_paths,
                            },
                        }
                else:
                    # Still check for backslashes
                    if '\\' in include_statement_value:
                        if path in results:
                            results[path][include_statement_value] = {
                                'actual_filenames': [None, ],
                                'actual_paths'    : [None, ],
                            }
                        else:
                            results[path] = {
                                include_statement_value: {
                                    'actual_filenames': [None, ],
                                    'actual_paths'    : [None, ],
                                },
                            }
            continue
        continue
    print("\n")
    print("Results:")
    print("========")
    n = len(results)
    print(
        f"Found {n} inconsistencies between the include statements and the actual "
        f"filenames in the filesystem.\n"
    )
    k = 0
    s = 0
    e = 0
    g = 0
    automatic = False
    for path in results.keys():
        k += 1
        print(f"File({k}/{n}): {path}")
        for include_statement_value, actual_filenames_and_paths in results[path].items():
            print(f"    '#include \"{include_statement_value}\"'")
            if len(actual_filenames_and_paths['actual_filenames']) == 1:
                print(f"        Should be:")
            else:
                print(f"        Should be one of:")
            correct_include_statement_values = []
            for j in range(len(actual_filenames_and_paths['actual_filenames'])):
                actual_filename = actual_filenames_and_paths['actual_filenames'][j]
                actual_path = actual_filenames_and_paths['actual_paths'][j]
                if actual_filename is None:
                    # Just correct the backslashes
                    correct_include_statement_values.append(
                        include_statement_value.replace('\\', '/')
                    )
                    print(f"        {j + 1}: '#include \"{correct_include_statement_values[-1]}\"'")
                else:
                    correct_include_statement_values.append(
                        include_statement_value.replace(
                            include_statement_value.replace('\\', '/').split('/')[-1], actual_filename
                        ).replace('\\', '/')
                    )
                    print(f"        {j + 1}: '#include \"{correct_include_statement_values[-1]}\"' ({actual_path})")
            print(f"        {j + 2}: Skip")
            print(f"        {j + 3}: Fix all {n} files automatically")
            print(f"        {j + 4}: Skip all - quit program")
            if not dry_run:
                if not automatic:
                    chosen_nr = input("        Choose a number and hit enter (no value = first choice): ")
                else:
                    chosen_nr = '1'
                if chosen_nr == '':
                    chosen_nr = '1'
                if chosen_nr == str(j + 2):
                    print(f"        Skipped.")
                    print("\n")
                    s += 1
                    continue
                if chosen_nr == str(j + 3):
                    automatic = True
                    print(f"        Fixing all automatically.")
                    print("\n")
                    chosen_nr = '1'
                if chosen_nr == str(j + 4):
                    print(f"        Quitting program.")
                    sys.exit(0)
                try:
                    chosen_nr = int(chosen_nr)
                except ValueError:
                    print(f"        Invalid choice. Skipped.")
                    print("\n")
                    s += 1
                    continue
                try:
                    correct_include_statement_value = correct_include_statement_values[chosen_nr - 1]
                except IndexError:
                    print(f"        Invalid choice. Skipped.")
                    print("\n")
                    s += 1
                    continue
                with open(os.path.join(root_dir, path), 'r', encoding='utf-8', errors='replace') as f:
                    old_content = f.read()
                correct_with_quotes = True
                new_content = old_content.replace(f'#include \"{include_statement_value}\"', f'#include \"{correct_include_statement_value}\"')
                if new_content == old_content:
                    # The include statement was probably with '<>' instead of '""'
                    correct_with_quotes = False
                    new_content = old_content.replace(f'#include <{include_statement_value}>', f'#include <{correct_include_statement_value}>')
                    if new_content == old_content:
                        print(f"        Unable to correct include statement. Do it manually. Skipped.")
                        print("\n")
                        e += 1
                        continue
                with open(os.path.join(root_dir, path), 'w', encoding='utf-8', errors='replace') as f:
                    f.write(new_content)
                if correct_with_quotes:
                    print(f"    Fixed include statement from '#include \"{include_statement_value}\"' to '#include \"{correct_include_statement_value}\"'.")
                else:
                    print(f"    Fixed include statement from '#include <{include_statement_value}>' to '#include <{correct_include_statement_value}>'.")
                g += 1
            print("\n")
            continue
        continue

    print(f"Summary:")
    print(f"========")
    print(f"Skipped: {s}")
    print(f"Fixed: {g}")
    print(f"Errors: {e}")
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=str(
            "Check the codebase for inconsistencies between the include statements in the files "
            "and the actual filenames in the filesystem."
        )
    )

    # Add arguments to the parser
    parser.add_argument(
        '-n',
        '--dry-run',
        action='store_true',
        help='Print the results without fixing the include statements',
    )
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The root directory of the codebase to check (default: .)',
        default=os.getcwd(),
    )

    # Override the default help message with a custom one
    parser.print_help = print_help

    # Parse the arguments. If the '-h' or '--help' argument is provided, the help message is printed
    # and the script exits automatically.
    args = parser.parse_args()

    # If this script runs in active mode (not dry-run), prompt the user first to confirm the action.
    if not args.dry_run:
        print(
            f"\n"
            f"WARNING:\n"
            f"This script will check the codebase for inconsistencies between the include\n"
            f"statements in the files and the actual filenames in the filesystem. It will\n"
            f"process the folder '{args.directory}'.\n"
            f"This action is irreversible. Type 'yes' to confirm you made a backup of the folder.\n"
            f"Type anything else to abort the operation.\n"
            f"\n"
        )
        response = input("Type 'yes' to confirm: ")
        if response.lower() == "yes":
            print("Confirmed. Starting the process.")
        else:
            print("Operation aborted. Showing help info...")
            print("\n")
            print_help()
            sys.exit(0)
    
    # Check the codebase for inconsistencies
    check_codebase(args.directory, args.dry_run)
    sys.exit(0)
