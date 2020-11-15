Release Procedure
=================

- Update the release notes:

  1. Review and cleanup ``doc/release/release_dev.rst``,

  2. Fix code in documentation by running
     ``cd doc && make doctest``.

  3. Make a list of merges and contributors by running
     ``doc/release/contribs.py <tag of previous release>``.

  4. Paste this list at the end of the ``release_dev.rst``. Scan the PR titles
     for highlights, deprecations, and API changes, and mention these in the
     relevant sections of the notes.

  5. Rename to ``doc/release/release_<major>.<minor>.rst``.

  6. Copy ``doc/release/release_template.rst`` to
     ``doc/release/release_dev.rst`` for the next release.

  7. Update ``doc/news.rst``.

- Commit changes::

   git commit -m "Release x.y.z"

- Add the version number as a tag in git::

   git tag -s [-u <key-id>] pykron-<major>.<minor> -m 'signed <major>.<minor> tag'

  (If you do not have a gpg key, use -m instead; it is important for
  Debian packaging that the tags are annotated)

- Push the new meta-data to github::

   git push --tags upstream master

  (where ``upstream`` is the name of the
   ``github.com:s4hri/pykron`` repository.)

- Review the github release page::

   https://github.com/s4hri/pykron/releases

- Publish on PyPi::

   git clean -fxd
   pip install -r requirements/release.txt
   python setup.py sdist bdist_wheel
   twine upload -s dist/*

- Update documentation on the web:
  The documentation is kept in a branch: s4hri/pykron gh-pages

- Prepare new version number in pykron/__init__.py

 - Commit and push changes::

    git add pykron/__init__.py
    git commit -m "New release version"
    git push upstream master
