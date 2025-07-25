# Copyright (c) 2017 Universidade Federal Fluminense (UFF)
# Copyright (c) 2017 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Dependency graph configuration"""

from collections import defaultdict

from future.utils import viewvalues

from ...utils.data import OrderedDefaultDict

from .synonymers import SameSynonymer, ReferenceSynonymer
from .synonymers import AccessNameSynonymer, JoinedSynonymer
from .filters import FilterAccessesOut, FilterInternalsOut
from .filters import FilterExternalAccessesOut, FilterTypesOut
from .filters import FilterWasDerivedFrom, FilterNotFromCodeOut
from .filters import FilterUseActivationName, FilterFuncOut
from .filters import JoinedFilter, AcceptAllNodesFilter
from .node_types import ClusterNode, EvaluationNode


class DependencyConfig(object):
    """Configure dependency graph"""

    # pylint: disable=too-many-instance-attributes
    # This is a configuration class. It is expected to have many attributes

    def __init__(self):
        self.rank_option = 0
        self.show_accesses = True
        self.show_internals = False
        self.show_external_files = False
        self.show_types = False
        self.show_timestamps = False
        self.activation_names = False
        self.combine_accesses = True
        self.combine_assignments = True
        self.combine_values = False
        self.show_only_was_derived_from = False
        self.show_only_was_derived_from_eid = None
        self.show_only_was_derived_from_trial = None
        self.hide_not_code = False
        self.hide_func = False
        self.max_depth = float("inf")
        self.mode = "simulation"

    @classmethod
    def create_arguments(cls, add_arg, mode="coarseGrain"):
        """Create arguments

        Arguments:
        add_arg -- add argument function
        """
        add_arg("-a", "--accesses", type=int, default=1, metavar="A",
                help="R|show file accesses (default: 1)\n"
                     "0 hides file accesses\n"
                     "1 shows each file once (hide external accesses)\n"
                     "2 shows each file once (show external accesses)\n"
                     "3 shows all accesses (except external accesses)\n"
                     "4 shows all accesses (including external accesses)")
        add_arg("-T", "--types", action="store_true",
                help="R|show type nodes.")
        add_arg("-t", "--hide-timestamps", action="store_false",
                help="hide timestamps")
        add_arg("-H", "--hide-internals", action="store_false",
                help="show variables and functions which name starts with a "
                     "leading underscore")
        add_arg("-hnc", "--hide-not-code", action="store_false",
                help="hide evaluations that aren't from the code")
        add_arg("-hf", "--hide-func", action="store_false",
                help="hide func type evaluations")
        add_arg("-an", "--activation-names", action="store_false",
                help="display nodes with their activation names instead")
        add_arg("-e", "--evaluations", type=int, default=1, metavar="E",
                help="R|combine evaluation nodes (default: 1)\n"
                     "0 does not combine evaluation nodes\n"
                     "1 combines evaluation nodes by assignment\n"
                     "2 combines evaluation nodes by value")
        add_arg("-d", "--depth", type=int, default=0, metavar="D",
                help="R|visualization depth (default: 0)\n"
                     "0 represents infinity\n"
                     "this parameter is ignored when the mode is \"all\"")
        add_arg("-g", "--group", type=int, default=0, metavar="R",
                help="R|align evalutions in the same column (default: 0)\n"
                     "0 does no align\n"
                     "1 aligns by line\n"
                     "2 aligns by line and column\n"
                     "With this option, all variables in a loop appear\n"
                     "grouped, reducing the width of the graph.\n"
                     "It may affect the graph legibility.\n"
                     "The alignment is independent for each activation.\n")
        add_arg("-m", "--mode", type=str, default=mode,
                choices=[
                    "activation", "coarseGrain", "looplessCoarseGrain", "fineGrain", "all"
                ],
                help=("R|Graph mode (default: {})\n"
                      "'activation' presents only function activations \n"
                      "and file accesses. Dependencies on the dataflow \n"
                      "are clustered by depth(-d).\n"
                       "'coarseGrain' is the same as the activation dataflow\n,"
                       "but with the addition of parameters and variable\n"
                       "assignment of function activations.\n"
                      "'looplessCoarseGrain' is the same as the coarseGrain\n"
                      "dataflow, but it doesn't repeat function activations\n"
                      "when they're in the same line in a loop.\n"
                      "'fineGrain' is the same as the coarseGrain dataflow\n"
                      "with the addition of variables, all user defined evaluations\n"
                      "and data values.\n"
                      "'all' presents a dataflow with all evaluations and\n"
                      "function activations. Dependencies on the dataflow are not clustered."
                      .format(mode)))
        add_arg("-w", "--wdf", type=int, 
                help="shows only one evaluation and the ones that derived it\n"
                "You must inform the evaluation's id")

    def read_args(self, args):
        """Read config from args"""
        self.show_accesses = bool(args.accesses)
        self.show_types = bool(args.types)
        self.show_timestamps = not bool(args.hide_timestamps)
        self.show_internals = not bool(args.hide_internals)
        self.hide_not_code = not bool(args.hide_not_code)
        self.activation_names = not bool(args.activation_names)
        self.hide_func = not bool(args.hide_func)
        self.show_external_files = args.accesses in {2, 4}

        self.combine_accesses = args.accesses in {1, 2}
        self.combine_assignments = args.evaluations == 1
        self.combine_values = args.evaluations == 2

        self.max_depth = args.depth or float("inf")
        self.rank_option = args.group
        self.mode = args.mode
        
        if(args.wdf):
            self.show_only_was_derived_from = True
            self.show_only_was_derived_from_trial = args.trial
            self.show_only_was_derived_from_eid = args.wdf

    def rank(self, cluster):
        """Group cluster evaluations"""
        if self.rank_option == 0:
            return
        by_line = OrderedDefaultDict(list)
        for node in cluster.elements:
            if not isinstance(node, EvaluationNode):
                continue
            #if isinstance(node, ClusterNode):
            #    continue
            if self.rank_option == 1:
                line = node.line
            else:
                line = (node.line, node.column)

            by_line[line].append(node)

        for eva_nids in viewvalues(by_line):
            cluster.ranks.append(eva_nids)

    def synonymer(self, extra=None):
        """Return synonymer based on config"""
        synonymers = []
        if self.combine_accesses:
            synonymers.append(AccessNameSynonymer())
        if self.combine_assignments:
            synonymers.append(SameSynonymer())
        if self.combine_values:
            synonymers.append(ReferenceSynonymer())
        synonymers.extend(extra or [])
        return JoinedSynonymer.create(*synonymers)

    def filter(self, extra=None):
        """Return filter based on config"""
        filters = []
        if not self.show_types:
            filters.append(FilterTypesOut())
        if not self.show_accesses:
            filters.append(FilterAccessesOut())
        elif not self.show_external_files:
            filters.append(FilterExternalAccessesOut())
        if not self.show_internals:
            filters.append(FilterInternalsOut())
        if self.show_only_was_derived_from:
            filters.append(FilterWasDerivedFrom(self.show_only_was_derived_from_eid, self.show_only_was_derived_from_trial))
        if self.hide_not_code:
            filters.append(FilterNotFromCodeOut())
        if self.activation_names:
            filters.append(FilterUseActivationName())
        if self.hide_func:
            filters.append(FilterFuncOut())
        filters.extend(extra or [])
        if not filters:
            return AcceptAllNodesFilter()
        return JoinedFilter.create(*filters)

    def clusterizer(self, trial, filter_=None, synonymer=None):
        """Return clusterizer based on config"""
        from .clusterizer import Clusterizer
        from .clusterizer import ActivationClusterizer
        from .clusterizer import DependencyClusterizer
        from .clusterizer import RetrospectiveClusterizer
        from .clusterizer import ProspectiveClusterizer
        cls = {
            "fineGrain": Clusterizer,
            "activation": ActivationClusterizer,
            "all": DependencyClusterizer,
            "coarseGrain": RetrospectiveClusterizer,
            "looplessCoarseGrain": ProspectiveClusterizer
        }[self.mode]
        return cls(
            trial,
            config=self,
            filter_=filter_,
            synonymer=synonymer
        )
