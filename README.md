# rdmo-plugins-readme

This repo implements a plugin for [RDMO](https://github.com/rdmorganiser/rdmo) to export one or multiple README files with information from your RDMO project's datasets.

## Setup

1. Install the plugin in your RDMO virtual environment using pip (directly from GitHub):

        ```bash
        pip install git+https://github.com/MPDL/rdmo-plugins-readme
        ```

2. Add "plain" to EXPORT_FORMATS in `config/settings/local.py`:

        ```python
        EXPORT_FORMATS = (
            ...
            ('plain', _('Plain Text'))
        )
        ```

3. Add the plugin to INSTALLED_APPS and PROJECT_EXPORTS in `config/settings/local.py`:

        ```python
        INSTALLED_APPS += ['rdmo_readme']

        PROJECT_EXPORTS += [
            ('rdmo-readme', _('RDMO README'), 'rdmo_readme.exports.ReadmeExport')
        ]
        ```

4. [Optional] Import [this view](https://github.com/MPDL/rdmo-plugins-readme/tree/main/view/rdmo-readme.xml) in your RDMO instance. This is the default view the plugin uses to create the README file but you can also provide your own view. If you do not import the view, you must provide your own view for the plugin to work.

## Usage

### Export plugins

Users can export README files created with the RDMO project's data.