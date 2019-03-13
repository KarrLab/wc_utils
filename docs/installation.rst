Installation
============

Prerequisites
--------------------------

First, install the third-party packages listed below. Detailed installation instructions are available in `An Introduction to Whole-Cell Modeling <http://docs.karrlab.org/intro_to_wc_modeling/master/0.0.1/installation.html>`_.

* `ChemAxon Marvin <https://chemaxon.com/products/marvin>`_: optional to calculate major protonation states

    * `Java <https://www.java.com>`_ >= 1.8

* `Git <https://git-scm.com/>`_
* `OpenBabel <http://openbabel.org>`_: optional to calculate chemical formulae
* `Pip <https://pip.pypa.io>`_ >= 18.0
* `Python <https://www.python.org>`_ >= 3.6

To use ChemAxon Marvin to calculate major protonation states, set ``JAVA_HOME`` to the path to your Java virtual machine (JVM) and add Marvin to the Java class path::

   export JAVA_HOME=/usr/lib/jvm/default-java
   export CLASSPATH=$CLASSPATH:/opt/chemaxon/marvinsuite/lib/MarvinBeans.jar


Latest release From PyPI
---------------------------
Run the following command to install the latest release from PyPI::

    pip install wc_utils[all]


Latest revision from GitHub
---------------------------
Run the following command to install the latest version from GitHub::

    pip install git+https://github.com/KarrLab/log.git#egg=log
    pip install git+https://github.com/KarrLab/pkg_utils.git#egg=pkg_utils[all]
    pip install git+https://github.com/KarrLab/wc_utils.git#egg=wc_utils[all]
