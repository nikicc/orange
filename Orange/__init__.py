from __future__ import absolute_import

import os
import sys
import warnings
import pkg_resources

from . import core

from . import orange, orangeom
sys.modules["orange"] = orange
sys.modules["orangeom"] = orangeom

# Little trick so that legacy imports work automatically
import Orange.orng
if Orange.orng.__path__[0] not in sys.path:
    sys.path = Orange.orng.__path__ + sys.path


ADDONS_ENTRY_POINT = 'orange.addons'


# Import helper
def _import(name):
    __import__(name, globals(), locals(), [], -1)


def _import_addons():
    globals_dict = globals()
    for entry_point in pkg_resources.iter_entry_points(ADDONS_ENTRY_POINT):
        try:
            module = entry_point.load()
            # Dot is not allowed in an entry point name (it should
            # be a Python identifier, because it is used as a class
            # name), so we are using __ instead
            name = entry_point.name.replace('__', '.')
            if '.' not in name:
                globals_dict[name] = module
            else:
                path, mod = name.rsplit('.', 1)
                parent_module_name = 'Orange.%s' % (path,)
                try:
                    parent_module = sys.modules[parent_module_name]
                except KeyError:
                    warnings.warn("Loading add-on '%s' failed because destination namespace point '%s' was not found." % (entry_point.name, parent_module_name), UserWarning, 2)
                    continue
                setattr(parent_module, mod, module)
            sys.modules['Orange.%s' % (name,)] = module
        except ImportError, err:
            warnings.warn("Importing add-on '%s' failed: %s" % (entry_point.name, err), UserWarning, 2)
        except pkg_resources.DistributionNotFound, err:
            warnings.warn("Loading add-on '%s' failed because of a missing dependency: '%s'" % (entry_point.name, err), UserWarning, 2)
        except Exception, err:
            warnings.warn("An exception occurred during the loading of '%s':\n%r" %(entry_point.name, err), UserWarning, 2)


_import("utils")

_import("data")
_import("data.io")
_import("data.sample")
_import("data.outliers")
_import("data.preprocess")
_import("data.preprocess.scaling")
_import("data.utils")
_import("data.discretization")
_import("data.continuization")
_import("data.filter")
_import("data.imputation")

_import("feature")
_import("feature.construction")
_import("feature.construction.functionDecomposition")
_import("feature.construction.univariate")
_import("feature.discretization")
_import("feature.imputation")
_import("feature.scoring")
_import("feature.selection")

_import("stat")

_import("statistics")
_import("statistics.estimate")
_import("statistics.contingency")
_import("statistics.distribution")
_import("statistics.basic")
_import("statistics.evd")

_import("classification")
_import("classification.tree")

_import("classification.rules")

_import("classification.lookup")
_import("classification.bayes")
_import("classification.svm")
_import("classification.logreg")
_import("classification.knn")
_import("classification.majority")
_import("classification.neural")

_import("tuning")

_import("projection")
_import("projection.linear")
_import("projection.mds")
_import("projection.som")

_import("ensemble")
_import("ensemble.bagging")
_import("ensemble.boosting")
_import("ensemble.forest")
_import("ensemble.stacking")

_import("regression")
_import("regression.base")
_import("regression.lasso")
_import("regression.linear")
_import("regression.mean")
_import("regression.pls")
_import("regression.tree")

_import("multilabel")
_import("multilabel.multibase")
_import("multilabel.br")
_import("multilabel.lp")
_import("multilabel.mlknn")
_import("multilabel.brknn")
_import("multilabel.mulan")

_import("associate")

_import("distance")

_import("wrappers")

_import("featureConstruction")
_import("featureConstruction.univariate")
_import("featureConstruction.functionDecomposition")

_import("evaluation")
_import("evaluation.scoring")
_import("evaluation.testing")

_import("clustering")
_import("clustering.kmeans")
_import("clustering.hierarchical")
_import("clustering.consensus")

_import("misc")

_import("utils")
_import("utils.environ")
_import("utils.counters")
_import("utils.addons")
_import("utils.render")
_import("utils.serverfiles")

_import_addons()

try:
    from . import version
    # Always use short_version here (see PEP 386)
    __version__ = version.short_version
    __git_revision__ = version.git_revision
except ImportError:
    __version__ = "unknown"
    __git_revision__ = "unknown"

del _import
del _import_addons
