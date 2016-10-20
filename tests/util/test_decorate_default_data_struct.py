""" Test decorate_default_data_struct.py

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-01
:Copyright: 2016, Karr Lab
:License: MIT
"""

from capturer import CaptureOutput
import unittest

from wc_utils.util.decorate_default_data_struct import default_mutable_params

class TestDefaultMutableParams(unittest.TestCase):

    @unittest.skip("skip, until capturer is working under pytest")
    def test_combinations(self):
        '''
        for perm in permutations:
            specify the right result
            create code implementing perm
            exec the code, and capture the result for testing
        '''

        NEW_DICT = '{}'
        OPTI_FUNC_DICT = 'd_dict={1:2}'
        FUNC_DICT_VAL = '{1: 2}'
        D_DICT = "'d_dict'"
        # This table provides the correct value for d_dict in auto_test(), given all 8
        # combinations of the values in the decorator, d_dict's default value, and 
        # d_dict's value in the call to auto_test()
    
        #         VV d_dict in decorator, 
        #                     VV d_dict default in auto_test
        #                                   VV d_dict in call to auto_test,
        #                                                   VV CORRECT d_dict in auto_test
        correct_values_in_auto_test = {
            (          '',  NEW_DICT,              ''):          NEW_DICT,
            (          '',  NEW_DICT,  OPTI_FUNC_DICT):     FUNC_DICT_VAL,
            (          '',    'None',              ''):            'None',
            (          '',    'None',  OPTI_FUNC_DICT):     FUNC_DICT_VAL,
            (      D_DICT,  NEW_DICT,              ''):          NEW_DICT,
            (      D_DICT,  NEW_DICT,  OPTI_FUNC_DICT):     FUNC_DICT_VAL,
            (      D_DICT,    'None',              ''):          NEW_DICT,
            (      D_DICT,    'None',  OPTI_FUNC_DICT):     FUNC_DICT_VAL
        }

        # test function and method calls
        # a test program with a function decorated by default_mutable_params
        # the test below instantiates this with all possible combinations of the three strings
        test_code="""
@default_mutable_params( [%s] )
def auto_test( d_dict=%s ):
    print(d_dict)
auto_test( %s )
        """

        test_class="""
class c(object):
    def __init__(self):
        pass

    @default_mutable_params( [ %s ] )
    def auto_test( self, d_dict=%s ):
        print(d_dict)

x=c()
x.auto_test( %s )
"""
        # Iterate over the 8 combinations
        for mutable_param_in_decorator in ['', D_DICT]:
            for param_default in [NEW_DICT, 'None']:
                for param_passed_to_func in ['', OPTI_FUNC_DICT]:
                
                    test_tuple = (mutable_param_in_decorator, param_default, param_passed_to_func)
                    correct_value = correct_values_in_auto_test[ test_tuple ]

                    code_instance = test_code % test_tuple 
                    with CaptureOutput() as capturer:
                        exec(code_instance)
                        out = capturer.get_text()
                    self.assertEquals( out, correct_value )

                    class_instance = test_class % test_tuple 
                    with CaptureOutput() as capturer:
                        exec(code_instance)
                        out = capturer.get_text()
                    self.assertEquals( out, correct_value )

