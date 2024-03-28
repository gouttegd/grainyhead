# -- General configuration ------------------------------------------------

source_suffix = '.rst'
master_doc = 'index'

copyright = u'2021,2022,2023,2024 Damien Goutte-Gattat'
author = u'Damien Goutte-Gattat <dpg44@cam.ac.uk>'

language = 'en'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'

extensions = ['sphinx.ext.intersphinx']
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for LaTeX output ---------------------------------------------

latex_engine = 'lualatex'

latex_elements = {'papersize': 'a4paper', 'pointsize': '10pt'}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        'GrainyHead.tex',
        u'GrainyHead Documentation',
        u'Damien Goutte-Gattat',
        'manual',
    ),
]

# -- Options for manual page output ---------------------------------------

man_pages = [(master_doc, 'grainyhead', u'GrainyHead Documentation', [author], 1)]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        'GrainyHead',
        u'GrainyHead Documentation',
        author,
        'GrainyHead',
        'Helper tools for GitHub.',
        'Miscellaneous',
    ),
]
