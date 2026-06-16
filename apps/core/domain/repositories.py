from abc import ABC, abstractmethod
from typing import Optional, TypeVar
from django.db.models import Model, QuerySet

ModelT = TypeVar('ModelT', bound=Model)


class Repository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[ModelT]:
        pass

    @abstractmethod
    def get_all(self) -> QuerySet[ModelT]:
        pass

    @abstractmethod
    def create(self, **kwargs) -> ModelT:
        pass

    @abstractmethod
    def update(self, id: int, **kwargs) -> Optional[ModelT]:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class DjangoRepository(Repository):
    """Base repository implementing Django ORM patterns"""
    model: type[ModelT] = None  # type: ignore[assignment]

    def __init__(self):
        if self.model is None:
            raise NotImplementedError("Subclasses must define model")

    def get_by_id(self, id: int) -> Optional[ModelT]:
        try:
            return self.model.objects.get(pk=id)
        except self.model.DoesNotExist:
            return None

    def get_all(self) -> QuerySet[ModelT]:
        return self.model.objects.all()

    def create(self, **kwargs) -> ModelT:
        return self.model.objects.create(**kwargs)

    def update(self, id: int, **kwargs) -> Optional[ModelT]:
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if instance:
            instance.delete()
            return True
        return False

    def filter(self, **kwargs) -> QuerySet[ModelT]:
        return self.model.objects.filter(**kwargs)

    def exclude(self, **kwargs) -> QuerySet[ModelT]:
        return self.model.objects.exclude(**kwargs)

    def annotate(self, *args, **kwargs) -> QuerySet[ModelT]:
        return self.model.objects.all().annotate(*args, **kwargs)

    def select_related(self, *fields) -> QuerySet[ModelT]:
        return self.model.objects.select_related(*fields)

    def prefetch_related(self, *fields) -> QuerySet[ModelT]:
        return self.model.objects.prefetch_related(*fields)

    def order_by(self, *fields) -> QuerySet[ModelT]:
        return self.model.objects.order_by(*fields)

    def count(self) -> int:
        return self.model.objects.count()

    def exists(self, **kwargs) -> bool:
        return self.model.objects.filter(**kwargs).exists()
