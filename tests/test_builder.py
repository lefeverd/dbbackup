import unittest
from pytest import raises

from dbbackup import builders


class TestBuilder(unittest.TestCase):
    def test_get_builder_module_mysql(self):
        module = builders.get_builder_module('mysql')
        assert module is not None

    def test_get_builder_class_mysql(self):
        module = builders.get_builder_module('mysql')
        builder_class = builders.get_builder_class(module, 'mysql')
        provider = builder_class()()
        assert isinstance(provider, builders.AbstractProvider)

    def test_get_provider_mysql(self):
        provider = builders.get('mysql')
        assert isinstance(provider, builders.AbstractProvider)

    def test_get_provider_unexisting(self):
        with raises(Exception) as e:
            builders.get('woops')
        assert 'Could not find' in e.value.args[0]
