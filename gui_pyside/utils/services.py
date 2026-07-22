# gui_pyside/utils/services.py
"""Reusable descriptors for lazy service initialization.

Usage::

    from gui_pyside.utils.services import LazyService
    from services.animal_service import AnimalService
    from services.muestra_service import MuestraService

    class MyDialog(BaseDialog):
        # Each line replaces ~10 lines of @property / @setter boilerplate
        animal_service = LazyService(AnimalService)
        muestra_service = LazyService(MuestraService)

The descriptor lazily creates the service on first attribute access and
supports dependency injection via normal assignment::

    dialog.animal_service = MockAnimalService()  # for tests
"""


class LazyService:
    """Descriptor that lazily instantiates a service class on first access.

    Uses Python's descriptor protocol (``__set_name__``, ``__get__``,
    ``__set__``) to transparently manage a private backing attribute
    (``_<name>``) while exposing a clean public name.

    * **Lazy init** — the service class is only called when the attribute
      is first read, not at ``__init__`` time.
    * **DI-friendly** — normal assignment (``self.service = MockSvc()``)
      stores the value in the backing attribute, so tests can inject
      mocks.
    * **Zero boilerplate** — replaces the repetitive
      ``@property`` / ``@<name>.setter`` / ``if self._x is None`` pattern
      that was copy-pasted across every dialog.
    """

    def __init__(self, service_class):
        self.service_class = service_class
        self.attr_name: str | None = None
        self.private_name: str | None = None

    def __set_name__(self, owner, name):
        """Called by the metaclass when the class is created.

        Stores the public attribute name and derives the private backing
        attribute name (``_<name>``).
        """
        self.attr_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        """Return the lazily-initialised service instance.

        When accessed on the *class* (``obj is None``), return the
        descriptor itself so that ``hasattr(MyDialog, 'service')`` still
        works and IDE introspection sees the descriptor.
        """
        if obj is None:
            return self
        value = getattr(obj, self.private_name, None)
        if value is None:
            value = self.service_class()
            setattr(obj, self.private_name, value)
        return value

    def __set__(self, obj, value):
        """Allow dependency injection by assigning a value directly.

        This is used in tests::

            dialog.animal_service = MockAnimalService()
        """
        setattr(obj, self.private_name, value)
