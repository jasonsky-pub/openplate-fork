# openplate

openplate is a cross-platform(Any Language, Any Computer), temPLATE tool for Micro-Environments (Microservices, Micro-UI, etc.)

## Purpose

**Problem:** Micro means more "setup and maintenance work".  **A lot more.**

**Solution:** OpenPlate is a CLI which generates and keeps your projects up to date.

## Installation with pip

To Install:

- Prerequisites: Openplate was developed using Python 3.11, so check that your local python is >= 3.11
- Type in your cli:
  
  ```
  pip install "git+https://github.com/Comcast/OpenPlate.git@main#egg=openplate"
  ```
### Security: init commands
For security, init commands are disabled by default.  In order to run many templates you must run this once:

```
openplate config set --allow-template-commands
```


## Example:
Using a template available in git at: `git@github.com:myorganization/ot-template-name#main`

```
openplate project init "git@github.com:myorganization/ot-template-name#main"
```

Other common examples:

Use an HTTPS Git URL:

```
openplate project init "https://github.com/my-org/ot-template.git#v1"
```

Use a local Git repository via `file://`:

```
openplate project init "file:///C:/repos/template-catalog#main"
```

Use a template stored in a sub-folder of a repository:

```
openplate project init "git@github.com:my-org/template-catalog.git?path=templates/net-api#v1"
```

Use the legacy `-r/--url` flag:

```
# deprecated format
openplate project init -r "https://github.com/my-org/ot-template.git#v1"
```

The `-n/--name` and `-f/--folder` init source options are no longer supported. Use explicit URLs instead.

openplate Will ask you some simple questions and then generate your project.

Done.

For more detailed command information, see [commands](docs/commands.md)

## Templating Info

For info on how to create templates:
[See Docs](docs/templates.md)

## Support and Contributions

If you need support, start by checking the [issues] page.
If that doesn't answer your questions, or if you think you found a bug,
please [file an issue].

That said, if you have questions, reach out to us
[communication].

Want to contribute to openplate? Awesome! Check out the [contributing](docs/contributing.md) guide.

## More information

Please see our [Docs](docs/readme.md)

# Creating a Release for Openplate

to create a release:

- As needed update the version in pyproject.toml
- In this folder, run "python -m build"
  - NOTE: If you run into an error "No module named build.__main__", first run "python -m pip install build" and try again
- Commit and push these changes to git before the next step
- Manually Upload the resulting files in "dist" to a new Release in github

# Verifying Installation

After updating run:

```
openplate --version
```

If it shows the current version, openplate is installed correctly.

# Installation Troubleshooting

If you run into not being able to run "openplate" after installing, the pip install location may not be in your path.

- Get the bin path:
  - During install, pip will tell you where it is installing to, for example it might install to: ```/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages```
  - Now remove "lib" and everything after it and replace it with bin:
  - ```/Library/Frameworks/Python.framework/Versions/3.11/bin```
- This path needs to be added to your path
  
  ## For Linux/Unix/Mac
  
  using your favorite editor, open ```~/.zshrc``` or ```~/.bash_profile``` depending on which shell you use
  
  ```
  nano ~/.bash_profile
  ```
  
  We need to add the following line at the end: (Make sure to replace the path used)
  
  ```
  export PATH='$PATH:/Library/Frameworks/Python.framework/Versions/3.11/bin'
  ```
  
  ## For windows
  
  Use your system dialog to add a new path for where it installed


