.. _contributor_guide:

Contributor Guide
=================

Pykron Development Workflow
---------------------------

1. Create a local copy

   * For the first-time contributor, here are the steps to create a copy of Pykron repository and submit pull requests

   * Go to `https://github.com/s4hri/pykron
     <https://github.com/s4hri/pykron>`_ and click the
     "fork" button to create your own copy of the project.

   * Clone the project to your local computer::

      git clone git@github.com:your-username/pykron.git

   * Navigate to the folder pykron and add the upstream repository for pull requests::

      git remote add upstream git@github.com:s4hri/pykron.git

   * Now, you have remote repositories named:

     - ``upstream``, which refers to the official ``pykron`` repository
     - ``origin``, which refers to your personal fork

   * Next, you need to set up your build environment.
     Here are instructions for using pip:
   
     * ``venv`` (pip based)
     
       ::
     
         # Create a virtualenv named ``pykron-dev`` that lives in the directory of
         # the same name
         python -m venv pykron-dev
         # or if your python 3.X binary is python3:
         python3 -m venv pykron-dev
         # Activate it
         source pykron-dev/bin/activate
         # Build and install pykron from source
         # Please make sure that you are still in pykron repository main directory
         pip install -e .
         # Test your installation
         PYTHONPATH=. pytest pykron
     

2. Develop your contribution:

   * Pull the latest changes from upstream::

      git checkout master
      git pull upstream master

   * Create a branch for the feature you want to work on. Since the
     branch name will appear in the merge message, use a sensible name
     such as 'bugfix-for-issue-1480'::

      git checkout -b bugfix-for-issue-1480

   * Commit locally as you progress (``git add`` and ``git commit``)

3. Test your contribution:

   * Run the test suite locally to see if the modifications alter any
     required functionalities::

      PYTHONPATH=. pytest pykron

4. Submit your contribution:

   * Push your changes back to your fork on GitHub::

      git push origin bugfix-for-issue-1480

   * Go to GitHub. The new branch will show up with a green Pull Request
     button---click it.

   * Add a short description when prompted.

5. Review process:

   * Reviewers (the other developers and interested community members) will
     write inline and/or general comments on your Pull Request (PR) to help
     you improve its implementation, documentation, and style.  Every single
     developer working on the project has their code reviewed, and we've come
     to see it as friendly conversation from which we all learn and the
     overall code quality benefits.  Therefore, please don't let the review
     discourage you from contributing: its only aim is to improve the quality
     of project, not to criticize (we are, after all, very grateful for the
     time you're donating!).

   * To update your pull request, make your changes on your local repository
     and commit. As soon as those changes are pushed up (to the same branch as
     before) the pull request will update automatically.

   .. note::

      If the PR closes an issue, make sure that GitHub knows to automatically
      close the issue when the PR is merged.  For example, if the PR closes
      issue number 1480, you could use the phrase "Fixes #1480" in the PR
      description or commit message.

6. Document changes

   If your change introduces any API modifications, please update
   ``doc/release/release_dev.rst``.

   If your change introduces a deprecation, add a reminder to
   ``doc/developer/deprecations.rst`` for the team to remove the
   deprecated functionality in the future.

   .. note::
   
      To reviewers: make sure the merge message has a brief description of the
      change(s) and if the PR closes an issue add, for example, "Closes #123"
      where 123 is the issue number.


Divergence from ``upstream master``
-----------------------------------

If GitHub indicates that the branch of your Pull Request can no longer
be merged automatically, merge the master branch into yours::

   git fetch upstream master
   git merge upstream/master

If any conflicts occur, they need to be fixed before continuing.  See
which files are in conflict using::

   git status

Which displays a message like::

   Unmerged paths:
     (use "git add <file>..." to mark resolution)

     both modified:   file_with_conflict.txt

Inside the conflicted file, you'll find sections like these::

   <<<<<<< HEAD
   The way the text looks in your branch
   =======
   The way the text looks in the master branch
   >>>>>>> master

Choose one version of the text that should be kept, and delete the
rest::

   The way the text looks in your branch

Now, add the fixed file::


   git add file_with_conflict.txt

Once you've fixed all merge conflicts, do::

   git commit

.. note::

   Advanced Git users are encouraged to `rebase instead of merge
   <https://networkx.org/documentation/stable/developer/gitwash/development_workflow.html#rebase-on-trunk>`__,
   but we squash and merge most PRs either way.


Guidelines
----------

* All new code functionality should have tests.
* All code should be documented, to the same
  `standard <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_
  as NumPy and SciPy.
* All changes are reviewed.  Ask on the
  `mailing list <http://groups.google.com/group/networkx-discuss>`_ if
  you get no response to your pull request.
* Default dependencies are listed in ``requirements/default.txt`` and extra
  (if ever needed) dependencies will be listed in ``requirements/extra.txt``.
* Use the following import conventions::

   from pykron.core import AsyncRequest
   from pykron.logging import PykronLogger



Testing
-------

``pykron`` has a basic test suite, which must be passed before
making a pull request to ensure all modifications conform to 
the basic requirements of what pykron offers in terms of
functionality.

We make use of the `pytest <https://docs.pytest.org/en/latest/>`__
testing framework, with tests located in ``pykron/tests`` subdirectories.

To run all tests::

    $ PYTHONPATH=. pytest pykron

Bugs
----

Please `report bugs on GitHub <https://github.com/s4hri/pykron/issues>`_.


Thanks
------

This guide is heavily based on the beautiful step-by-step _CONTRIBUTING.rst by networkx/networkx project on GitHub.