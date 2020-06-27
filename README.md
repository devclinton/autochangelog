<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview 

Autochangelog can automatically generate a changelog for your project. Currently, the changelog contents can ben 
generated directly from git commit log or from GitHub Issues. It can output JSON, Markdown, or Restructured Text(Sphinx)

# Installing

To install use

```bash
pip install autochangelog
``` 

You can also install the latest development version from github using

```bash
pip install git+https://github.com/devclinton/autochangelog.git#egg=autochangelog
```

# Basic Usage

You can see the options for autochangelog by running `autochangelog --help`

```bash
$ autochangelog --help
Usage: autochangelog [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug
  --verbose / --no-verbose
  --help                    Show this message and exit.

Commands:
  generate

```

* *Verbose* - Enable Verbose logging
* *Debug* - Enable debug logging
* *COMMAND* - Currently only generate is supported

You can see the supported source locations for the changelog data by running `autochangelog generate --help`

```bash
$ autochangelog generate --help
Usage: autochangelog generate [OPTIONS] COMMAND1 [ARGS]... [COMMAND2
                              [ARGS]...]...

Options:
  --help  Show this message and exit.

Commands:
  git       † Warning: could not load plugin. See `autochangelog git --help`.
  github    † Warning: could not load plugin. See `autochangelog github
            --help`.

  json      Generate changelog as a JSON
  markdown  Generate changelog as a Markdown file
```

## Git Commit Log

You can generate a commit log directly from a Git Commit Log by using the Git Src

```bash
autochangelog generate git --help
Usage: autochangelog generate git [OPTIONS] SRC

  Get changelog using a Git repo

Options:
  --version TEXT
  -e, --exclude TEXT
  --help              Show this message and exit.
```

Using the git commit source, you must always specify a path to a git repo that has been checkout out

For example, on the autochangelog repo, if I run this command
```bash
 autochangelog generate git . json
```

You would get an output of 
```json
{
    "Development": {
        "Fix doc": [
            "Fix doc"
        ],
        "autochangelog": [
            "autochangelog"
        ]
    }
}
```

Where git log returns
```bash
$ git log
commit e2650fc07dceb732e1a77c2fbddcaf21771ff6e7 (HEAD -> master, origin/master)
Author: Clinton Collins <clinton.collins@gmail.com>
Date:   Mon Jun 22 10:04:25 2020 -0700

    Fix doc

commit 0837f221dfb5f617ac324520ffcbd271d34f1b4a
Author: Clinton Collins <clinton.collins@gmail.com>
Date:   Sat Jun 20 16:58:53 2020 -0700

    autochangelog
```

```bash
 autochangelog generate git . markdown
```
The output will be like
```bash
Changelog
=========

* [Development]


== Development

* [0837f22]( 0837f221dfb5f617ac324520ffcbd271d34f1b4a) - autochangelog
* [e2650fc]( e2650fc07dceb732e1a77c2fbddcaf21771ff6e7) - Fix doc
```
