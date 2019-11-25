"""
abc-classroom.clone
======================

"""

import csv
from pathlib import Path
import glob
from shutil import copy

from . import config as cf
from . import github
from . import utils


def clone_or_update_repo(organization, repo, clone_dir, skip_existing):
    """
    Tries to clone the repository 'repo' from the organization. If the local
    repository already exists, pulls instead of cloning (unless the skip flag
    is set, in which case it does nothing).
    """
    destination_dir = Path(clone_dir, repo)
    if destination_dir.is_dir():
        # if path exists, pull instead of clone (unless skip_existing)
        if skip_existing:
            print(
                "Local repo {} already exists; skipping".format(
                    destination_dir
                )
            )
            return
        github.pull_from_github(destination_dir)
    else:
        github.clone_repo(organization, repo, clone_dir)


def clone_student_repos(args):
    """Iterates through the student roster, clones each repo for this
    assignment into the directory specified in the config, and then copies the notebook files into the nbgrader 'submitted' directory, if nbgrader_dir set in config.yml."""

    assignment = args.assignment
    skip_existing = args.skip_existing

    print("Loading configuration from config.yml")
    config = cf.get_config()
    roster_filename = cf.get_config_option(config, "roster", True)
    course_dir = cf.get_config_option(config, "course_directory", True)
    clone_dir = cf.get_config_option(config, "clone_dir", True)
    organization = cf.get_config_option(config, "organization", True)
    nbgrader_dir = cf.get_config_option(config, "nbgrader_dir", False)

    if nbgrader_dir is None:
        print(
            "nbgrader_dir is not set in config.yml. Will not copy any assignment files."
        )
    try:
        Path(course_dir, clone_dir).mkdir(exist_ok=True)
        missing = []
        with open(roster_filename, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                student = row["github_username"]
                # expected columns are identifier,github_username,github_id,name
                repo = "{}-{}".format(assignment, student)
                try:
                    clone_or_update_repo(
                        organization, repo, clone_dir, skip_existing
                    )
                    if nbgrader_dir is not None:
                        copy_assignment_files(
                            clone_dir, nbgrader_dir, student, assignment
                        )
                except RuntimeError as err:
                    missing.append(repo)
        if len(missing) == 0:
            print("All successful; no missing repos")
        else:
            print("Could not clone or update the following repos: ")
            for r in missing:
                print(" {}".format(r))

    except FileNotFoundError as err:
        print("Cannot find roster file".format(roster_filename))
        print(err)


def copy_assignment_files(clone_dir, nbgrader_dir, student, assignment):
    # make sure the nbgrader directory exists

    repo = "{}-{}".format(assignment, student)
    files = Path(clone_dir, repo).glob("*.ipynb")
    destination = Path(nbgrader_dir, "submitted", student, assignment)
    destination.mkdir(parents=True, exist_ok=True)
    for f in files:
        print("copying {} to {}".format(f, destination))
        copy(f, destination)
