""" Utilities for linear and quadratic programming.

The module supports two types of problems:

* Linear problems

    .. math::

        \text{Maximize}~c' x \\
        \text{Subject to} \\
            A x = b \\
            x_l <= x <= x_u

* Quadratic problems

    .. math::

        \text{Maximize}~\frac{1}{2} x' Q x + c' x \\
        \text{Subject to} \\
            A x = b \\
            x_l <= x <= x_u

The module support five types of variables:

* binary
* integer
* continuous
* semi-integer
* semi-continuous

The module support several solvers:

* Open-source

    * COIN-OR `Cbc <https://projects.coin-or.org/Cbc>`_, Cgl, and Clp via `CyLP <http://mpy.github.io/CyLPdoc>`_
    * `GLPK <https://www.gnu.org/software/glpk>`_ via `optlang <http://optlang.readthedocs.io>`_
    * `SciPy <https://docs.scipy.org>`_

* Commercial with free academic licenses

    * `FICO XPRESS <http://www.fico.com/en/products/fico-xpress-optimization>`_
    * `IBM CPLEX <https://www-01.ibm.com/software/commerce/optimization/cplex-optimizer>`_
    * `Gurobi <http://www.gurobi.com/products/gurobi-optimizer>`_
    * `Mosek <https://www.mosek.com>`_

Note: GLPK and SciPy only support linear programming

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-11-14
:Copyright: 2017, Karr Lab
:License: MIT
"""

import abc
import enum
import numpy
import optlang
import os
import six
import sympy

try:
    import cplex
except ImportError:
    pass

try:
    import cylp
except ImportError:
    pass

try:
    import gurobi
except ImportError:
    pass

try:
    import mosek
except ImportError:
    pass

try:
    import xpress
except ImportError:
    pass


class VariableType(enum.Enum):
    """ Variable type """
    binary = 0
    continuous = 1
    integer = 2
    semi_integer = 3
    semi_continuous = 4


class ObjectiveDirection(enum.Enum):
    """ Direction to solve a mathematical problem """
    max = 0
    maximize = 0
    min = 1
    minimize = 1


class ProblemType(enum.Enum):
    """ Problem type """
    fixed_milp = 0
    fixed_miqp = 1
    lp = 1
    milp = 2
    miqp = 3
    qp = 4


class Solver(enum.Enum):
    """ Solver """
    cbc = 0
    cplex = 1
    glpk = 2
    gurobi = 3
    mosek = 4
    scipy = 5
    xpress = 6


class Presolve(enum.Enum):
    """ Presolve mode """
    auto = 0
    on = 1
    off = 2


class Verbosity(enum.Enum):
    """ Verbosity level """
    off = 0
    status = 1
    warning = 2
    error = 3


class StatusCode(enum.Enum):
    """ Status code for the result of solving a mathematical problem """
    optimal = 0
    infeasible = 1
    other = 2


class ExportFormat(enum.Enum):
    """ Export format """
    alp = 0
    dpe = 1
    dua = 2
    lp = 3
    mps = 4
    ppe = 5
    rew = 6
    rlp = 7
    sav = 8


class Variable(object):
    """ A variable

    Attributes:
        name (:obj:`str`): name
        type (:obj:`VariableType`): type        
        lower_bound (:obj:`float`): lower bound
        upper_bound (:obj:`float`): upper bound
        primal (:obj:`float`): primal value
        reduced_cost (:obj:`float`): reduced cost
    """

    def __init__(self, name='', type=VariableType.continuous, lower_bound=None, upper_bound=None):
        """
        Args:
            name (:obj:`str`, optional): name
            type (:obj:`VariableType`, optional): type
            lower_bound (:obj:`float`, optional): lower bound
            upper_bound (:obj:`float`, optional): upper bound            
        """
        self.name = name
        self.type = type
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.primal = float('nan')
        self.reduced_cost = float('nan')


class Term(object):
    """ Term (of an objective or contraint)

    Attributes:
        coefficient (:obj:`float`): coefficient
    """

    def __init__(self, coefficient):
        """
        Args:
            coefficient (:obj:`float`): coefficient
        """
        self.coefficient = coefficient


class LinearTerm(Term):
    """ Linear term (of an objective or contraint)

    Attributes:
        variable (:obj:`Variable`): variable
    """

    def __init__(self, variable, coefficient):
        """
        Args:
            variable (:obj:`Variable`): variable
            coefficient (:obj:`float`): coefficient
        """
        self.variable = variable
        self.coefficient = coefficient


class QuadraticTerm(Term):
    """ Quadtratic term (of an objective or contraint)

    Attributes:
        variable_1 (:obj:`Variable`): first variable
        variable_2 (:obj:`Variable`): second variable
    """

    def __init__(self, variable_1, variable_2, coefficient):
        """
        Args:
            variable_1 (:obj:`Variable`): first variable
            variable_2 (:obj:`Variable`): second variable
            coefficient (:obj:`float`): coefficient
        """
        self.variable_1 = variable_1
        self.variable_2 = variable_2
        self.coefficient = coefficient


class Constraint(object):
    """ A constraint

    Attributes:
        name (:obj:`str`): name
        terms (:obj:`list` of :obj:`Term`): the variables and their coefficients
        lower_bound (:obj:`float`): lower bound
        upper_bound (:obj:`float`): upper bound
        dual (:obj:`float`): dual value
    """

    def __init__(self, name='', terms=None, lower_bound=None, upper_bound=None):
        """
        Args:
            name (:obj:`str`, optional): name
            terms (:obj:`list` of :obj:`Term`, optional): the variables and their coefficients
            lower_bound (:obj:`float`, optional): lower bound
            upper_bound (:obj:`float`, optional): upper bound
        """
        self.name = name
        self.terms = terms or []
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.dual = float('nan')


class SolveOptions(object):
    """ Options for :obj:`Problem.solve`

    Attributes:
        solver (:obj:`Solver`): solver
        presolve (:obj:`Presolve`): presolve
        verbosity (:obj:`Verbosity`): determines how much status, warnings, and errors is printed out
    """

    def __init__(self, solver=Solver.cplex, presolve=Presolve.on, verbosity=Verbosity.off):
        """
        Args:
            solver (:obj:`Solver`, optional): solver
            presolve (:obj:`Presolve`, optional): presolve
            verbosity (:obj:`Verbosity`, optional): determines how much status, warnings, and errors is printed out
        """
        self.solver = solver
        self.presolve = presolve
        self.verbosity = verbosity


class Problem(object):
    """ A mathematical problem

    Attributes:
        name (:obj:`str`): name
        variables (:obj:`list` of :obj:`Variable`): the variables, :math:`x`
        objective_direction (:obj:`ObjectiveDirection`): objective direction
        objective_terms (:obj:`list` of :obj:`LinearTerm`): the elements of the objective, :math:`c` and :math:`Q`
        constraints (:obj:`list` of :obj:`LinearTerm`): the constraints, :math:`A` and :math:`b`
    """

    def __init__(self, name='', variables=None, objective_direction=ObjectiveDirection.max, objective_terms=None, constraints=None):
        """
        Args:
            name (:obj:`str`, optional): name
            variables (:obj:`list` of :obj:`Variable`, optional): the variables, :math:`x`
            objective_direction (:obj:`ObjectiveDirection`, optional): objective direction
            objective_terms (:obj:`list` of :obj:`LinearTerm`, optional): the elements of the objective, :math:`c` and :math:`Q`
            constraints (:obj:`list` of :obj:`LinearTerm`, optional): the constraints, :math:`A` and :math:`b`
        """
        self.name = name
        self.variables = variables or []
        self.objective_direction = objective_direction
        self.objective_terms = objective_terms or []
        self.constraints = constraints or []

    def get_problem_type(self):
        """ Get the type of the problem

        Returns:
            :obj:`ProblemType`: problem type
        """
        has_integer = False
        for variable in self.variables:
            if variable.type in [VariableType.binary, VariableType.integer, VariableType.semi_integer]:
                has_integer = True
                break

        is_linear = True
        for term in self.objective_terms:
            if isinstance(term, QuadraticTerm):
                is_linear = False
                break

        if is_linear:
            if has_integer:
                return ProblemType.milp
            else:
                return ProblemType.lp
        else:
            if has_integer:
                return ProblemType.miqp
            else:
                return ProblemType.qp

    def convert(self, options=None):
        """ Generate a data structure for the problem for another package

        Args:
            options (:obj:`SolveOptions`, optional): options

        Returns:
            :obj:`object`: problem in a data structure for another package

        Raises:
            :obj:`Exception`: if the solver is not supported
        """

        options = options or SolveOptions()

        if options.solver == Solver.cbc:
            return CbcSolver(options).convert(self)
        elif options.solver == Solver.cplex:
            return CplexSolver(options).convert(self)
        elif options.solver == Solver.glpk:
            return GlpkSolver(options).convert(self)
        elif options.solver == Solver.gurobi:
            return GurobiSolver(options).convert(self)
        elif options.solver == Solver.mosek:
            return MosekSolver(options).convert(self)
        elif options.solver == Solver.scipy:
            return ScipySolver(options).convert(self)
        elif options.solver == Solver.xpress:
            return XpressSolver(options).convert(self)
        else:
            raise Exception('Unsupported solver "{}"'.format(options.solver))

    def solve(self, options=None):
        """ Solve the problem

        Args:
            options (:obj:`SolveOptions`, optional): options

        Returns:
            :obj:`Result`: result

        Raises:
            :obj:`Exception`: if the solver is not supported
        """

        options = options or SolveOptions()

        # solve problem
        if options.solver == Solver.cbc:
            result = CbcSolver(options).solve(self)
        elif options.solver == Solver.cplex:
            result = CplexSolver(options).solve(self)
        elif options.solver == Solver.glpk:
            result = GlpkSolver(options).solve(self)
        elif options.solver == Solver.gurobi:
            result = GurobiSolver(options).solve(self)
        elif options.solver == Solver.mosek:
            result = MosekSolver(options).solve(self)
        elif options.solver == Solver.scipy:
            result = ScipySolver(options).solve(self)
        elif options.solver == Solver.xpress:
            result = XpressSolver(options).solve(self)
        else:
            raise Exception('Unsupported solver "{}"'.format(options.solver))

        # assign primal and dual attributes of the variables and constriants
        self._assign_result(result)

        # return result
        return result

    def _assign_result(self, result):
        """ Assign primal and dual attributes of the variables and constriants

        Args:
            result (:obj:`Result`): result
        """
        for variable, primal, reduced_cost in zip(self.variables, result.primals, result.reduced_costs):
            variable.primal = primal
            variable.reduced_cost = reduced_cost

        for constraint, dual in zip(self.constraints, result.duals):
            constraint.dual = dual

    def export(self, filename, format=None):
        """ Export a problem to a file in one of these support formats

        * **alp**: problem with generic names in lp format, where the variable names are annotated to indicate the type and bounds of each variable
        * **dpe**: dual perturbed problem
        * **dua**: dual
        * **lp**
        * **mps**
        * **ppe**: perturbed problem
        * **rew**: problem with generic names in mps format
        * **rlp**: problem with generic names in lp format
        * **sav**

        Args:            
            filename (:obj:`str`): path to save problem
            format (:obj:`str`, optional): export format; if the format is not provided, the 
                format is inferred from the filename

        Raises:
            :obj:`Exception`: if the format is not supported
        """
        if not format:
            format = os.path.splitext(filename)[1][1:]

        if format in ['sav', 'mps', 'lp', 'rew', 'rlp', 'alp', 'dua', 'emb', 'ppe', 'dpe']:
            with CplexSolver().convert(self) as cplex:
                cplex.write(filename, filetype=format)
        else:
            # todo: use other packages to support more formats
            raise Exception('Unsupported format "{}"'.format(format))


class SolverInterface(six.with_metaclass(abc.ABCMeta, object)):
    """ A solver

    Attributes:
        options (:obj:`SolveOptions`): options
    """

    def __init__(self, options=None):
        """
        Args:
            options (:obj:`SolveOptions`, optional): options
        """
        self.options = options or SolveOptions()

    @abc.abstractmethod
    def convert(self, problem):
        """ Convert a problem to the data structure of the solver

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in the data structure of the solver

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    @abc.abstractmethod
    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        pass


class CbcSolver(SolverInterface):
    """ COIN-OR Cbc solver """

    def convert(self, problem):
        """ Convert a problem to Cbc's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in Cbc's data structure

        Raises:
            ::obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        import cylp

        return Result(status_code, status_message, value, primals, dual)


class CplexSolver(SolverInterface):
    """ IBM CPLEX solver """

    def convert(self, problem):
        """ Convert a problem to CPLEX's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`cplex.Cplex`: the problem in CPLEX's data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """

        cpx = cplex.Cplex()
        cpx.set_problem_name(problem.name)

        # set verbosity
        if self.options.verbosity.value < Verbosity.status.value:
            cpx.set_results_stream(None)
        if self.options.verbosity.value < Verbosity.warning.value:
            cpx.set_warning_stream(None)
        if self.options.verbosity.value < Verbosity.error.value:
            cpx.set_error_stream(None)

        # create variables and set bounds
        cplex_types = cpx.variables.type

        names = []
        types = []
        lb = []
        ub = []

        for variable in problem.variables:
            names.append(variable.name)

            if variable.type == VariableType.binary:
                types.append(cplex_types.binary)
            elif variable.type == VariableType.integer:
                types.append(cplex_types.integer)
            elif variable.type == VariableType.continuous:
                types.append(cplex_types.continuous)
            elif variable.type == VariableType.semi_integer:
                types.append(cplex_types.semi_integer)
            elif variable.type == VariableType.semi_continuous:
                types.append(cplex_types.semi_continuous)
            else:
                raise Exception('Unsupported variable of type "{}"'.format(variable.type))

            if variable.lower_bound is not None:
                lb.append(variable.lower_bound)
            else:
                lb.append(-1 * cplex.infinity)

            if variable.upper_bound is not None:
                ub.append(variable.upper_bound)
            else:
                ub.append(cplex.infinity)
        cpx.variables.add(names=names, types=types, lb=lb, ub=ub)

        # set objective
        if problem.objective_direction.value == ObjectiveDirection.max.value:
            cpx.objective.set_sense(cpx.objective.sense.maximize)
        elif problem.objective_direction.value == ObjectiveDirection.min.value:
            cpx.objective.set_sense(cpx.objective.sense.minimize)
        else:
            raise Exception('Unsupported objective direction "{}"'.format(problem.objective_direction))

        for term in problem.objective_terms:
            if isinstance(term, LinearTerm):
                i = problem.variables.index(term.variable)
                cpx.objective.set_linear(i, cpx.objective.get_linear(i) + term.coefficient)
            elif isinstance(term, QuadraticTerm):
                i_1 = problem.variables.index(term.variable_1)
                i_2 = problem.variables.index(term.variable_2)
                cpx.objective.set_quadratic_coefficients(i_1, i_2, cpx.objective.get_quadratic_coefficients(i_1, i_2) + term.coefficient)
            else:
                raise Exception('Unsupported objective term of type "{}"'.format(term.__class__.__name__))

        # set constraints
        names = []
        lin_expr = []
        senses = []
        rhs = []
        range_values = []
        for constraint in problem.constraints:
            if constraint.lower_bound is None and constraint.upper_bound is None:
                continue
            if constraint.lower_bound is None:
                senses.append('L')
                rhs.append(constraint.upper_bound)
                range_values.append(0.)
            elif constraint.upper_bound is None:
                senses.append('G')
                rhs.append(constraint.lower_bound)
                range_values.append(0.)
            elif constraint.lower_bound == constraint.upper_bound:
                senses.append('E')
                rhs.append(constraint.lower_bound)
                range_values.append(0.)
            else:
                senses.append('R')
                rhs.append(constraint.lower_bound)
                range_values.append(constraint.upper_bound - constraint.lower_bound)

            names.append(constraint.name)

            ind = []
            val = []
            for term in constraint.terms:
                if not isinstance(term, LinearTerm):
                    raise Exception('Unsupported constraint term of type "{}"'.format(term.__class__.__name__))
                ind.append(problem.variables.index(term.variable))
                val.append(term.coefficient)
            lin_expr.append(cplex.SparsePair(ind=ind, val=val))

        cpx.linear_constraints.add(names=names, lin_expr=lin_expr, senses=senses, rhs=rhs, range_values=range_values)

        # set problem type
        problem_type = problem.get_problem_type()
        if problem_type == ProblemType.lp:
            cpx.set_problem_type(cpx.problem_type.LP)
        elif problem_type == ProblemType.qp:
            cpx.set_problem_type(cpx.problem_type.LP)
        elif problem_type == ProblemType.milp:
            cpx.set_problem_type(cpx.problem_type.LP)
        elif problem_type == ProblemType.miqp:
            cpx.set_problem_type(cpx.problem_type.LP)
        elif problem_type == ProblemType.fixed_milp:
            cpx.set_problem_type(cpx.problem_type.LP)
        elif problem_type == ProblemType.fixed_miqp:
            cpx.set_problem_type(cpx.problem_type.LP)
        else:
            raise Exception('Unsupported problem type "{}"'.format(problem_type))

        return cpx

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """

        with self.convert(problem) as cpx:
            # set presolve
            if self.options.presolve == Presolve.on:
                cpx.parameters.preprocessing.presolve.set(cpx.parameters.preprocessing.presolve.values.on)
            elif self.options.presolve == Presolve.off:
                pass
                cpx.parameters.preprocessing.presolve.set(cpx.parameters.preprocessing.presolve.values.off)
            else:
                raise Exception('Unsupported presolve model "{}"'.format(self.options.presolve))

            cpx.solve()
            sol = cpx.solution

            tmp = sol.get_status()
            if tmp in [1, 101]:
                status_code = StatusCode.optimal
            elif tmp in [3, 103]:
                status_code = StatusCode.infeasible
            else:
                status_code = StatusCode.other

            status_message = sol.get_status_string()
            value = sol.get_objective_value()

            primals = numpy.array(sol.get_values())
            reduced_costs = numpy.array(sol.get_reduced_costs())
            duals = numpy.array(sol.get_dual_values())

        return Result(status_code, status_message, value, primals, reduced_costs, duals)


class GlpkSolver(SolverInterface):
    """ GLPK solver """

    def convert(self, problem):
        """ Convert a problem to GPLK's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`optlang.glpk_interface.Model`: the problem in GLPK's data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        model = optlang.glpk_interface.Model(name=problem.name)

        if self.options.presolve == Presolve.auto:
            model.configuration.presolve = 'auto'
        elif self.options.presolve == Presolve.on:
            model.configuration.presolve = True
        elif self.options.presolve == Presolve.off:
            model.configuration.presolve = False
        else:
            raise Exception('Unsupported presolve model "{}"'.format(self.options.presolve))
        model.configuration.verbosity = self.options.verbosity.value

        # variables
        optlang_variables = []
        for variable in problem.variables:
            if variable.type == VariableType.binary:
                type = 'binary'
            elif variable.type == VariableType.integer:
                type = 'integer'
            elif variable.type == VariableType.continuous:
                type = 'continuous'
            else:
                raise Exception('Unsupported variable type "{}"'.format(variable.type))
            optlang_variable = optlang.glpk_interface.Variable(
                name=variable.name, lb=variable.lower_bound, ub=variable.upper_bound, type=type)
            model.add(optlang_variable)
            optlang_variables.append(optlang_variable)

        # objective
        if problem.objective_direction.value == ObjectiveDirection.max.value:
            direction = 'max'
        elif problem.objective_direction.value == ObjectiveDirection.min.value:
            direction = 'min'
        else:
            raise Exception('Unsupported objective direction "{}"'.format(problem.objective_direction))

        expr = sympy.Integer(0)
        for term in problem.objective_terms:
            if isinstance(term, LinearTerm):
                expr += sympy.Float(term.coefficient) * optlang_variables[problem.variables.index(term.variable)]
            elif isinstance(term, QuadraticTerm):
                expr += sympy.Float(term.coefficient) \
                    * optlang_variables[problem.variables.index(term.variable_1)] \
                    * optlang_variables[problem.variables.index(term.variable_2)]
            else:
                raise Exception('Unsupported objective term of type "{}"'.format(term.__class__.__name__))
        model.objective = optlang.glpk_interface.Objective(expr, direction=direction)

        # constraints
        for constraint in problem.constraints:
            expr = sympy.Integer(0)
            for term in constraint.terms:
                if isinstance(term, LinearTerm):
                    expr += sympy.Float(term.coefficient) * optlang_variables[problem.variables.index(term.variable)]
                else:
                    raise Exception('Unsupported constraint term of type "{}"'.format(term.__class__.__name__))
            model.add(optlang.glpk_interface.Constraint(expr, lb=constraint.lower_bound, ub=constraint.upper_bound, name=constraint.name))

        # return model
        return model

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        model = self.convert(problem)

        model.optimize()

        if model.status == 'optimal':
            status_code = StatusCode.optimal
        elif model.status == 'infeasible':
            status_code = StatusCode.infeasible
        else:
            status_code = StatusCode.other
        status_message = model.status

        value = model.objective.value
        primals = numpy.array(list(model.primal_values.values()))
        reduced_costs = numpy.array(list(model.reduced_costs.values()))
        duals = numpy.array(list(model.shadow_prices.values()))

        return Result(status_code, status_message, value, primals, reduced_costs, duals)


class GurobiSolver(SolverInterface):
    """ Gurobi solver """

    def convert(self, problem):
        """ Convert a problem to Gurobi's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in Gurobi's data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """

        import gurobipy
        return Result(status_code, status_message, value, primals, reduced_costs, dual)


class MosekSolver(SolverInterface):
    """ Mosek solver """

    def convert(self, problem):
        """ Convert a problem to Mosek's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in Mosek's data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        import mosek

        return Result(status_code, status_message, value, primals, reduced_costs, dual)


class ScipySolver(SolverInterface):
    """ SciPy solver """

    def convert(self, problem):
        """ Convert a problem to SciPy's data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in SciPy's data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        import scipy

        return Result(status_code, status_message, value, primals, reduced_costs, dual)


class XpressSolver(SolverInterface):
    """ FICO XPRESS solver """

    def convert(self, problem):
        """ Convert a problem to XPRESS' data structure

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`object`: the problem in XPRESS' data structure

        Raises:
            :obj:`Exception`: if the presolve mode is unsupported, a variable has an unsupported type, 
                an objective direction is unsupported, an objective has an unsupported term, a constraint 
                has an unsupported term, or the problem is not of a supported type
        """
        pass

    def solve(self, problem):
        """ Solve the problem

        Args:
            problem (:obj:`Problem`): problem

        Returns:
            :obj:`Result`: result
        """
        import xpress

        return Result(status_code, status_message, value, primals, reduced_costs, dual)


class Result(object):
    """ The result of solving a mathematical problem

    Attributes:
        status_code (:obj:`StatusCode`): status code
        status_message (:obj:`str`): status message
        value (:obj:`float`): objective value
        primals (:obj:`numpy.ndarray`): primal values
        reduced_costs (:obj:`numpy.ndarray`): reduced costs
        duals (:obj:`numpy.ndarray`): dual values/shadow prices
    """

    def __init__(self, status_code, status_message, value, primals, reduced_costs, duals):
        """
        Args:
            status_code (:obj:`StatusCode`): status code
            status_message (:obj:`str`): status message
            value (:obj:`float`): objective value
            primals (:obj:`numpy.ndarray`): primal values
            reduced_costs (:obj:`numpy.ndarray`): reduced costs
            duals (:obj:`numpy.ndarray`): dual values/reduced costs/shadow prices
        """
        self.status_code = status_code
        self.status_message = status_message
        self.value = value
        self.primals = primals
        self.reduced_costs = reduced_costs
        self.duals = duals
