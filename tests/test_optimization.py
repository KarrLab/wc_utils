""" Tests for the the optimization module

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-11-14
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils import optimization
import numpy
import os
import shutil
import sympy
import tempfile
import unittest

try:
    import cplex
    has_cplex = True
except ImportError:
    has_cplex = False

try:
    import cylp
    has_cbc = True
except ImportError:
    has_cbc = False

try:
    import gurobipy
    has_gurobi = True
except ImportError:
    has_gurobi = False

try:
    import mosek
    has_mosek = True
except ImportError:
    has_mosek = False

try:
    import xpress
    has_xpress = True
except ImportError:
    has_xpress = False


class TestLinearOptimization(unittest.TestCase):

    def setUp(self):
        self.problem = prob = optimization.Problem(name='test-lp')

        # variables
        ex_a = optimization.Variable(name='ex_a', lower_bound=0, upper_bound=1)
        prob.variables.append(ex_a)

        r1 = optimization.Variable(name='r1', lower_bound=0)
        prob.variables.append(r1)

        r2 = optimization.Variable(name='r2', lower_bound=0)
        prob.variables.append(r2)

        r3 = optimization.Variable(name='r3', lower_bound=0)
        prob.variables.append(r3)

        r4 = optimization.Variable(name='r4', lower_bound=0)
        prob.variables.append(r4)

        biomass_production = optimization.Variable(name='biomass_production', lower_bound=0)
        prob.variables.append(biomass_production)

        ex_biomass = optimization.Variable(name='ex_biomass', lower_bound=0)
        prob.variables.append(ex_biomass)

        # constraints
        prob.constraints.append(optimization.Constraint(name='a', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=ex_a, coefficient=1),
            optimization.LinearTerm(variable=r1, coefficient=-1),
        ]))
        prob.constraints.append(optimization.Constraint(name='b', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=r1, coefficient=1),
            optimization.LinearTerm(variable=r2, coefficient=-1),
            optimization.LinearTerm(variable=r3, coefficient=-1),
        ]))
        prob.constraints.append(optimization.Constraint(name='c', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=r2, coefficient=1),
        ]))
        prob.constraints.append(optimization.Constraint(name='d', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=r2, coefficient=1),
            optimization.LinearTerm(variable=r4, coefficient=-1),
        ]))
        prob.constraints.append(optimization.Constraint(name='e', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=r3, coefficient=2),
            optimization.LinearTerm(variable=r4, coefficient=1),
            optimization.LinearTerm(variable=biomass_production, coefficient=-1),
        ]))
        prob.constraints.append(optimization.Constraint(name='biomass', upper_bound=0, lower_bound=0, terms=[
            optimization.LinearTerm(variable=biomass_production, coefficient=1),
            optimization.LinearTerm(variable=ex_biomass, coefficient=-1),
        ]))

        # objective
        prob.objective_direction = optimization.ObjectiveDirection.maximize
        prob.objective_terms = [optimization.LinearTerm(variable=biomass_production, coefficient=1.)]

    def test_get_problem_type(self):
        self.assertEqual(self.problem.get_problem_type(), optimization.ProblemType.lp)

    @unittest.skip('todo')
    def test_cbc_solve(self):
        self._test_solve('cbc')

    @unittest.skipUnless(has_cplex, 'CPLEX is not installed')
    def test_cplex_convert(self):
        import cplex

        cpx = self.problem.convert(optimization.SolveOptions(solver=optimization.Solver.cplex))

        self.assertEqual(cpx.get_problem_name(), 'test-lp')

        self.assertEqual(cpx.get_problem_type(), cpx.problem_type.LP)

        self.assertEqual(cpx.variables.get_names(), ['ex_a', 'r1', 'r2', 'r3', 'r4', 'biomass_production', 'ex_biomass'])
        self.assertEqual(set(cpx.variables.get_lower_bounds()), set([0.]))
        self.assertEqual(cpx.variables.get_upper_bounds(),
                         [1., cplex.infinity, cplex.infinity, cplex.infinity, cplex.infinity, cplex.infinity, cplex.infinity])
        self.assertEqual(cpx.variables.get_num(), 7)
        self.assertEqual(cpx.variables.get_num_binary(), 0)
        self.assertEqual(cpx.variables.get_num_integer(), 0)
        self.assertEqual(cpx.variables.get_num_semiinteger(), 0)
        self.assertEqual(cpx.variables.get_num_semicontinuous(), 0)

        self.assertEqual(cpx.objective.get_sense(), cpx.objective.sense.maximize)
        self.assertEqual(cpx.objective.get_linear(), [0., 0., 0., 0., 0., 1., 0.])
        self.assertEqual(cpx.objective.get_quadratic(), [])

        self.assertEqual(cpx.linear_constraints.get_names(), ['a', 'b', 'c', 'd', 'e', 'biomass'])
        self.assertEqual(set(cpx.linear_constraints.get_senses()), set(['E']))
        self.assertEqual(set(cpx.linear_constraints.get_rhs()), set([0.]))
        self.assertEqual(set(cpx.linear_constraints.get_range_values()), set([0.]))
        self.assertEqual(cpx.linear_constraints.get_num_nonzeros(), 13)
        self.assertEqual(cpx.linear_constraints.get_coefficients(0, 0), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(0, 1), -1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(1, 1), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(1, 2), -1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(1, 3), -1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(2, 2), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(3, 2), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(3, 4), -1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(4, 3), 2)
        self.assertEqual(cpx.linear_constraints.get_coefficients(4, 4), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(4, 5), -1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(5, 5), 1)
        self.assertEqual(cpx.linear_constraints.get_coefficients(5, 6), -1)

        self.assertEqual(cpx.quadratic_constraints.get_num(), 0)

    @unittest.skipUnless(has_cplex, 'CPLEX is not installed')
    def test_cplex_solve(self):
        self._test_solve('cplex')

    def test_glpk_convert(self):
        glpk = self.problem.convert(optimization.SolveOptions(solver=optimization.Solver.glpk))

        self.assertEqual(glpk.name, 'test-lp')

        self.assertEqual(glpk.variables.keys(), ['ex_a', 'r1', 'r2', 'r3', 'r4', 'biomass_production', 'ex_biomass'])
        self.assertEqual(set([v.lb for v in glpk.variables]), set([0.]))
        self.assertEqual([v.ub for v in glpk.variables], [1., None, None, None, None, None, None])
        self.assertEqual(set([v.type for v in glpk.variables]), set(['continuous']))

        self.assertEqual(glpk.objective.direction, 'max')
        self.assertEqual(glpk.objective.expression, 1. * glpk.variables[-2])

        self.assertEqual([c.name for c in glpk.constraints], ['a', 'b', 'c', 'd', 'e', 'biomass'])
        self.assertEqual(set([c.lb for c in glpk.constraints]), set([0.]))
        self.assertEqual(set([c.ub for c in glpk.constraints]), set([0.]))
        self.assertEqual(sympy.simplify(glpk.constraints[0].expression - (1. * glpk.variables[0] - 1. * glpk.variables[1])), 0)
        self.assertEqual(sympy.simplify(glpk.constraints[1].expression -
                                        (1. * glpk.variables[1] - 1. * glpk.variables[2] - 1. * glpk.variables[3])), 0)
        self.assertEqual(sympy.simplify(glpk.constraints[2].expression - (1. * glpk.variables[2])), 0)
        self.assertEqual(sympy.simplify(glpk.constraints[3].expression - (1. * glpk.variables[2] - 1. * glpk.variables[4])), 0)
        self.assertEqual(sympy.simplify(glpk.constraints[4].expression -
                                        (2. * glpk.variables[3] + 1. * glpk.variables[4] - 1. * glpk.variables[5])), 0)
        self.assertEqual(sympy.simplify(glpk.constraints[5].expression - (1. * glpk.variables[5] - 1. * glpk.variables[6])), 0)

    def test_glpk_solve(self):
        self._test_solve('glpk')

    @unittest.skip('todo')
    def test_gurobi_solve(self):
        self._test_solve('gurobi')

    @unittest.skip('todo')
    def test_mosek_solve(self):
        self._test_solve('mosek')

    @unittest.skip('todo')
    def test_scipy_solve(self):
        self._test_solve('scipy')

    @unittest.skip('todo')
    def test_xpress_solve(self):
        self._test_solve('xpress')

    def _test_solve(self, solver):
        result = self.problem.solve(optimization.SolveOptions(solver=optimization.Solver[solver]))
        self.assertEqual(result.status_code, optimization.StatusCode.optimal)
        self.assertEqual(result.status_message, 'optimal')
        self.assertEqual(result.value, 2.)

        numpy.testing.assert_array_equal(result.primals, numpy.array([1., 1., 0., 1., 0., 2., 2.]))

        self.assertEqual(result.reduced_costs[0], 2)
        self.assertEqual(result.reduced_costs[1], 0)
        #self.assertEqual(result.reduced_costs[2], -1)
        self.assertEqual(result.reduced_costs[3], 0)
        self.assertEqual(result.reduced_costs[4], 0)
        self.assertEqual(result.reduced_costs[5], 0)
        self.assertEqual(result.reduced_costs[6], 0)

        self.assertEqual(result.duals[0], -2)
        self.assertEqual(result.duals[1], -2)
        #self.assertEqual(result.duals[2], 0)
        self.assertEqual(result.duals[3], -1)
        self.assertEqual(result.duals[4], -1)
        self.assertEqual(result.duals[5], 0)

    def test__assign_result(self):
        problem = self.problem

        primals = 1. * numpy.array(range(len(problem.variables)))
        reduced_costs = 2. * numpy.array(range(len(problem.variables)))
        duals = 3. * numpy.array(range(len(problem.constraints)))
        result = optimization.Result(None, None, None, primals, reduced_costs, duals)

        problem._assign_result(result)

        self.assertEqual(self.problem.variables[0].primal, 0.)
        self.assertEqual(self.problem.variables[1].primal, 1.)
        self.assertEqual(self.problem.variables[2].primal, 2.)
        self.assertEqual(self.problem.variables[3].primal, 3.)
        self.assertEqual(self.problem.variables[4].primal, 4.)
        self.assertEqual(self.problem.variables[5].primal, 5.)
        self.assertEqual(self.problem.variables[6].primal, 6.)

        self.assertEqual(self.problem.variables[0].reduced_cost, 0.)
        self.assertEqual(self.problem.variables[1].reduced_cost, 2.)
        self.assertEqual(self.problem.variables[2].reduced_cost, 4.)
        self.assertEqual(self.problem.variables[3].reduced_cost, 6.)
        self.assertEqual(self.problem.variables[4].reduced_cost, 8.)
        self.assertEqual(self.problem.variables[5].reduced_cost, 10.)
        self.assertEqual(self.problem.variables[6].reduced_cost, 12.)

        self.assertEqual(self.problem.constraints[0].dual, 0.)
        self.assertEqual(self.problem.constraints[1].dual, 3.)
        self.assertEqual(self.problem.constraints[2].dual, 6.)
        self.assertEqual(self.problem.constraints[3].dual, 9.)
        self.assertEqual(self.problem.constraints[4].dual, 12.)
        self.assertEqual(self.problem.constraints[5].dual, 15.)

    def test_export(self):
        dirname = tempfile.mkdtemp()

        def test_format(format):
            filename = os.path.join(dirname, 'tmp.' + format)
            self.problem.export(filename)
            self.assertTrue(os.path.isfile(filename))

        test_format('alp')
        test_format('dpe')
        test_format('dua')
        test_format('lp')
        test_format('mps')
        test_format('ppe')
        test_format('rew')
        test_format('rlp')
        test_format('sav')

        shutil.rmtree(dirname)


class TestQuadtraticOptimization(unittest.TestCase):
    pass
