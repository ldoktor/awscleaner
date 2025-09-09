AWSCleaner
==========

simple project built around [awsweeper](https://github.com/jckuester/awsweeper)
to delete only old resources.

The main limitation of awsweeper is that it's stateless, therefore resources
that do not support ``createat`` can't be deleted after specified period.
This project uses awsweeper to get to-be-cleaned resources, compares it to
previous state and remembers where it seen each item for the first time.
Then it allows specifying an age and ignores newer resources.

Following command will execute ``awsweeper --dry-run awsweeper_config.yaml``,
compares the output to ``resources.yaml``, adds new items using current
``time.time()`` and generates ``cleanup.yaml`` with resources that were seen
more than 2 weeks ago::

    awscleaner --awsweeper-args awsweeper_config.yaml --age 2w resources.yaml cleanup.yaml

One can also use ``s3://`` prefix for ``resources.yaml`` and ``cleanup.yaml``
to get/push the files from s3.
