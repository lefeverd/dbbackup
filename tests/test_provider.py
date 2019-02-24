from dbbackup import providers


class TestProvider:
    def test_not_is_concrete_provider_abstract_provider(self):
        assert providers.is_concrete_provider(
            providers.AbstractProvider) is False

    def test_not_is_concrete_provider_not_subclass(self):
        assert providers.is_concrete_provider(object) is False

    def test_is_concrete_provider(self):
        class ConcreteProvider(providers.AbstractProvider):
            pass

        ConcreteProvider.__abstractmethods__ = set()
        assert providers.is_concrete_provider(ConcreteProvider) is True

    def test_get_provider_module_mysql(self):
        module = providers.get_provider_module('mysql')
        assert module is not None

    def test_get_provider_class_mysql(self):
        module = providers.get_provider_module('mysql')
        provider_class = providers.get_provider_class(module)
        assert isinstance(provider_class(), providers.AbstractProvider)

    def test_get_provider_mysql(self):
        provider = providers.get('mysql')
        assert isinstance(provider, providers.AbstractProvider)
