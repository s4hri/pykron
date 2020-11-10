# Building docs

We use Sphinx for generating the API and reference documentation.

Pre-built versions can be found at

    https://github.com/s4hri/pykron/tree/gh-pages

for both the stable and the latest (i.e., development) releases.

## Instructions

After installing Pykron please check the required Python packages:

    cat requirements/doc.txt
    pip install -r requirements/doc.txt

in the root directory.

To build the HTML documentation, clone the gh-pages branch as
pykron-gh-pages next to the pykron repository, and enter::

    make html

in the ``doc/`` directory.

This will generate a ``../../pykron-gh-pages/html`` subdirectory
containing the built documentation.

To build the PDF documentation, enter::

    make latexpdf

You will need to have LaTeX installed for this.
