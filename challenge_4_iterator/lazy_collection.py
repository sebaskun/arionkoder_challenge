from functools import reduce as functools_reduce


class LazyCollection:
    """
    A collection that lazily evaluates transformations.

    This class wraps any iterable and allows you to chain operations
    (map, filter, chunk) without immediately executing them. The operations
    are only evaluated when you iterate over the collection.
    """

    def __init__(self, source):
        """
        Initialize the lazy collection with a data source (list, generator, file, etc.).
        """
        self._source = source

    def map(self, transform):
        """
        Apply a transformation to each element (lazily).
        """
        transformed = (transform(item) for item in self._source)
        return LazyCollection(transformed)

    def filter(self, predicate):
        """
        Filter elements based on a condition (lazily).
        """
        filtered = (item for item in self._source if predicate(item))
        return LazyCollection(filtered)

    def chunk(self, size: int):
        """
        Split the collection into chunks of a given size (lazily).
        """
        def chunk_generator():
            iterator = iter(self._source)
            while True:
                chunk = []
                for _ in range(size):
                    try:
                        chunk.append(next(iterator))
                    except StopIteration:
                        if chunk:  # Yield partial chunk if any items collected
                            yield chunk
                        return

                yield chunk

        return LazyCollection(chunk_generator())

    def reduce(self, reducer, initial = None):
        """
        Reduce the collection to a single value (eager operation).
        """
        if initial is None:
            # If no initial value, use the first element
            return functools_reduce(reducer, self._source)
        else:
            return functools_reduce(reducer, self._source, initial)

    def take(self, n: int):
        """
        Take only the first n elements (lazily).
        """
        def take_generator():
            count = 0
            for item in self._source:
                if count >= n:
                    return
                yield item
                count += 1

        return LazyCollection(take_generator())

    def __iter__(self):
        """
        Make the collection iterable.
        """
        return iter(self._source)

    def to_list(self):
        return list(self._source)
