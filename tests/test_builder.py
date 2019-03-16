from pytest import raises

from dbbackup import providers


class TestBuilder:
    def test_get_builder_module_mysql(self):
        module = providers.get_builder_module('mysql')
        assert module is not None

    def test_get_builder_class_mysql(self):
        module = providers.get_builder_module('mysql')
        builder_class = providers.get_builder_class(module, 'mysql')
        provider = builder_class()()
        assert isinstance(provider, providers.AbstractProvider)

    def test_get_provider_mysql(self):
        provider = providers.get('mysql')
        assert isinstance(provider, providers.AbstractProvider)

    def test_get_provider_unexisting(self):
        with raises(ImportError) as e:
            providers.get('woops')
        assert 'Could not find' in e.value.msg
